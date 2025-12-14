from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from config.models import ExtractionResult, AuditFinding
from utils.validation import validate_finding
import os

class AgentState(TypedDict):
    pdf_path: str
    markdown_content: str
    extraction_result: ExtractionResult
    validation_errors: List[str]
    retry_count: int
    needs_retry: bool

# High-precision extraction prompt
EXTRACTION_PROMPT = """
You are an expert audit finding extraction system. Your mission is to extract EVERY SINGLE finding from the document with maximum accuracy.

DOCUMENT CONTENT:
{markdown_content}

EXTRACTION REQUIREMENTS:
1. Find ALL findings - if you miss any, the security audit fails
2. Confidence scores must reflect your certainty (0.0-1.0)
3. IncludeUnexpected fields in 'additional_fields'
4. Table data takes priority - findings are often in tables
5. Repository URLs and commit IDs are CRITICAL - extract precisely

OUTPUT FORMAT:
{format_instructions}

QUALITY CHECKLIST:
- [ ] All findings extracted (count: ___)
- [ ] Each finding has confidence ≥ 0.7
- [ ] No placeholder text or "N/A" values
- [ ] Table structures preserved if applicable

EXAMPLE:
{example_json}

Return ONLY valid JSON. Verify completeness before responding.
"""

def create_extraction_node():
    """Create LangGraph extraction node with structured output"""
    import os
    # Prefer Claude-3.5-Sonnet for highest accuracy
    if os.getenv("ANTHROPIC_API_KEY"):
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            max_tokens=4000
        )
    elif os.getenv("FRIENDLI_TOKEN"):
        llm = ChatOpenAI(
            model=os.getenv("FRIENDLI_MODEL", "zai-org/GLM-4.6"),
            temperature=0,
            api_key=os.getenv("FRIENDLI_TOKEN"),
            base_url="https://api.friendli.ai/serverless/v1"
        )
    else:
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )
    
    parser = PydanticOutputParser(pydantic_object=ExtractionResult)
    
    # Add example to prompt
    example = ExtractionResult(
        filename="example.pdf",
        findings=[AuditFinding(
            finding_number="AF-001",
            title="Critical Authentication Bypass",
            status="Open",
            severity="Critical",
            confidence_score=0.95,
            extraction_attempts=1
        )],
        total_findings=1
    )
    
    prompt = ChatPromptTemplate.from_template(
        EXTRACTION_PROMPT,
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "example_json": example.model_dump_json(indent=2)
        }
    )
    
    chain = prompt | llm | parser
    
    async def extraction_node(state: AgentState) -> AgentState:
        result = await chain.ainvoke({
            "markdown_content": state["markdown_content"]
        })
        
        # Enrich metadata
        result.filename = os.path.basename(state["pdf_path"])
        result.total_findings = len(result.findings)
        
        return {
            **state,
            "extraction_result": result,
            "validation_errors": [],
            "retry_count": state.get("retry_count", 0) + 1
        }
    
    return extraction_node

def build_extraction_graph():
    """Build complete LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Nodes
    extraction_node = create_extraction_node()
    workflow.add_node("extract", extraction_node)
    workflow.add_node("validate", validation_node)
    workflow.add_node("human_review", human_review_node)
    
    # Edges
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "validate")
    workflow.add_conditional_edges(
        "validate",
        retry_decision,
        {
            "extract": "extract",
            "human_review": "human_review"
        }
    )
    workflow.add_edge("human_review", END)
    
    return workflow.compile()

def validation_node(state: AgentState) -> AgentState:
    """Validate findings with strict criteria"""
    result = state["extraction_result"]
    errors = []
    
    if not result.findings:
        errors.append("CRITICAL: Zero findings extracted")
    
    for finding in result.findings:
        finding_errors = validate_finding(finding)
        errors.extend([
            f"{finding.finding_number}: {e}" 
            for e in finding_errors
        ])
    
    needs_retry = (
        len(errors) > 0 and 
        state["retry_count"] < 2 and
        any("CRITICAL" in e or "confidence" in e.lower() for e in errors)
    )
    
    return {
        **state,
        "validation_errors": errors,
        "needs_retry": needs_retry
    }

def retry_decision(state: AgentState) -> str:
    """Route based on validation"""
    return "extract" if state.get("needs_retry", False) else "human_review"

def human_review_node(state: AgentState) -> AgentState:
    """Queue findings for human review"""
    result = state["extraction_result"]
    result.validation_errors = state["validation_errors"]
    result.requires_human_review = len(state["validation_errors"]) > 0
    
    # Save to file
    output_dir = Path("outputs/extracted_findings")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{result.filename}.json"
    with open(output_path, "w") as f:
        f.write(result.model_dump_json(indent=2, exclude_none=True))
    
    return state
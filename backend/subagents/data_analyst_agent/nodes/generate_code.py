import pathlib
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import DataAnalystState
from ..validator_agent import run_validator_agent

# Configure the LLM; you can change the model name as needed.
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# Load the prompt template from the prompts folder.
_PROMPT_PATH = pathlib.Path(__file__).resolve().parent.parent / "prompts" / "code_generation_prompt.txt"
_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(_PROMPT_PATH.read_text(encoding="utf-8"))


def generate_code_node(state: DataAnalystState) -> DataAnalystState:
    """
    Node 1: ask the LLM to generate Python analysis/dashboard code.
    - Input: file_path, user_request
    - Output: code (Python source string) added to state
    """
    file_path = state.get("file_path")
    user_request = state.get("user_request", "")

    if not file_path:
        state["error"] = "generate_code_node: 'file_path' is required in state."
        return state

    logs = state.get("logs", [])
    logs.append(f"generate_code_node: Generating code for file {file_path!r}")
    state["logs"] = logs

    # Step 0: run validator to ensure the request matches available columns
    validation_state = run_validator_agent(file_path, user_request)

    state["validation_columns"] = validation_state.get("columns", [])
    state["validation_missing_columns"] = validation_state.get("missing_columns", [])
    state["validation_warnings"] = validation_state.get("warnings", [])

    # If validator already found a fatal error, propagate and stop
    if validation_state.get("error") and not validation_state.get("rewritten_request"):
        state["error"] = validation_state["error"]
        logs.append(f"generate_code_node: Validation failed - {validation_state['error']}")
        state["logs"] = logs
        return state

    # Use rewritten request if available; otherwise keep the original
    validated_request = validation_state.get("rewritten_request") or user_request
    state["validated_request"] = validated_request

    # Render prompt
    prompt = _PROMPT_TEMPLATE.format(
        file_path=file_path,
        user_request=validated_request,
    )

    # Call LLM
    response = _llm.invoke(prompt)
    raw = (response.content or "").strip()

    # Clean common markdown fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        # drop opening fence
        lines = lines[1:]
        # drop closing fence if present
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines)

    code = raw.strip()

    state["code"] = code
    return state

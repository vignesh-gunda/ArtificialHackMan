from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI

# SubAgents
from .normal_chat_agent import NormalChatAgent

# Optional subagents (placeholders)
from subagents.ocr_extractor_agent.deepagent_subsystem import OCRExtractorSubAgent
from subagents.data_analyst_agent.deepagent_subsystem import DataAnalystSubAgent
from subagents.video_generator_agent.deepagent_subsystem import VideoGeneratorSubAgent

def create_supervisor():
    """
    Creates the main DeepAgent Supervisor that routes user requests
    to the correct sub-agent automatically.
    """

    # Main brain LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Register available sub-agents
    subagents = [
        NormalChatAgent(),
        OCRExtractorSubAgent(),      # placeholder
        DataAnalystSubAgent(),       # placeholder
        VideoGeneratorSubAgent(),    # placeholder
    ]

    # Build the DeepAgent Supervisor
    agent = DeepAgent(
        llm=llm,
        subagents=subagents,
        max_iters=8,   # reasonable default
        verbose=True,
    )

    return agent

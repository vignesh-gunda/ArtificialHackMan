from langchain_deepagents import SubAgent
from langchain_openai import ChatOpenAI

class NormalChatAgent(SubAgent):
    """
    Handles general conversational queries.
    Acts like ChatGPT-style chat inside DeepAgent.
    """
    name = "chat"

    def run(self, user_input: str):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke(user_input)
        return response.content

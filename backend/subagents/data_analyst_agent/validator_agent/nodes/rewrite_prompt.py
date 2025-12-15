from langchain_openai import ChatOpenAI

from ..state import ValidatorState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


def rewrite_prompt_node(state: ValidatorState) -> ValidatorState:
    if state.get("valid"):
        state["rewritten_request"] = state["user_request"]
        state["warnings"] = []
        return state

    missing = state.get("missing_columns", [])
    cols = state.get("columns", [])

    repair_instruction = f"""
The user requested columns that do not exist in the dataset: {missing}.

Available columns are:
{cols}

Rewrite their request so it uses only valid column names, keeping the intent as close as possible.
If it is impossible to satisfy their intent, clearly state so.
Respond with a concise rewritten request.
"""

    rewritten = llm.invoke(repair_instruction).content.strip()
    state["rewritten_request"] = rewritten
    state["warnings"] = [f"Columns not found: {', '.join(missing)}"] if missing else []
    return state

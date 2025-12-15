from langgraph.graph import StateGraph, END
from .state import ValidatorState
from .nodes.validate_columns import validate_columns_node
from .nodes.rewrite_prompt import rewrite_prompt_node


def build_validator_agent():
    graph = StateGraph(ValidatorState)

    graph.add_node("validate_columns", validate_columns_node)
    graph.add_node("rewrite_prompt", rewrite_prompt_node)

    graph.set_entry_point("validate_columns")
    graph.add_edge("validate_columns", "rewrite_prompt")
    graph.add_edge("rewrite_prompt", END)

    return graph.compile()


_validator_app = None


def get_validator_app():
    global _validator_app
    if _validator_app is None:
        _validator_app = build_validator_agent()
    return _validator_app


def run_validator_agent(file_path: str, user_request: str) -> ValidatorState:
    app = get_validator_app()
    initial_state: ValidatorState = {
        "file_path": file_path,
        "user_request": user_request,
    }
    return app.invoke(initial_state)

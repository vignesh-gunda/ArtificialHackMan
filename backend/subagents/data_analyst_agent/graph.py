from langgraph.graph import StateGraph, END

from .state import DataAnalystState
from .nodes import generate_code_node, execute_code_node


def build_data_analyst_agent():
    """
    Build and compile the data analyst subagent graph.
    The graph:
        entry -> generate_code -> execute_code -> END
    """
    graph = StateGraph(DataAnalystState)

    graph.add_node("generate_code", generate_code_node)
    graph.add_node("execute_code", execute_code_node)

    graph.set_entry_point("generate_code")
    graph.add_edge("generate_code", "execute_code")
    graph.add_edge("execute_code", END)

    return graph.compile()


# Convenience function for direct use from Deep Agent / backend
_data_analyst_app = None


def get_data_analyst_app():
    global _data_analyst_app
    if _data_analyst_app is None:
        _data_analyst_app = build_data_analyst_agent()
    return _data_analyst_app


def run_data_analyst_agent(
    file_path: str,
    user_request: str,
) -> DataAnalystState:
    """
    Helper: run the subagent once and return the final state.

    Intended to be called by your Deep Agent or backend like:
        final_state = run_data_analyst_agent(file_path, "Create EDA dashboard")
        html = final_state["html_content"]
    """
    app = get_data_analyst_app()
    initial_state: DataAnalystState = {
        "file_path": file_path,
        "user_request": user_request,
        "logs": [],
    }
    return app.invoke(initial_state)

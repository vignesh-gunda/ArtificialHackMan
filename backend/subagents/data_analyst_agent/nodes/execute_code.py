from ..state import DataAnalystState
from ..sandbox import SandboxRunner


def execute_code_node(state: DataAnalystState) -> DataAnalystState:
    """
    Node 2: execute the generated Python code in the sandbox and
    capture the resulting dashboard.html content.
    - Input: code
    - Output: html_content, html_path, error
    """
    code = state.get("code")
    if not code:
        state["error"] = "execute_code_node: No 'code' found in state."
        return state

    logs = state.get("logs", [])
    logs.append("execute_code_node: Executing generated code in sandbox.")
    state["logs"] = logs

    runner = SandboxRunner()

    # workspace_name can be anything; could be user/session-specific.
    html_content, error = runner.run_python_code(code, workspace_name="data_analyst_agent")

    if error:
        state["error"] = error
    else:
        state["html_content"] = html_content
        state["html_path"] = "run_workspaces/data_analyst_agent/dashboard.html"

    return state

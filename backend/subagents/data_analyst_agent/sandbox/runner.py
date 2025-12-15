import os
import pathlib
import traceback
from typing import Tuple, Optional


class SandboxRunner:
    """
    Simple sandbox abstraction.
    - For now, executes code locally in a dedicated working directory.
    - You can later replace the internals with e2b or Daytona, keeping the same interface.
    """

    def __init__(self, base_dir: str = "run_workspaces"):
        self.base_dir = pathlib.Path(base_dir).resolve()
        self.base_dir.mkdir(exist_ok=True)

    def run_python_code(
        self,
        code: str,
        workspace_name: str = "default",
        expected_html: str = "dashboard.html",
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Execute the given Python code in an isolated working directory.

        Returns:
            (html_content, error_message)
        """
        workdir = self.base_dir / workspace_name
        workdir.mkdir(exist_ok=True)

        html_path = workdir / expected_html
        error: Optional[str] = None
        html_content: Optional[str] = None

        old_cwd = os.getcwd()
        try:
            os.chdir(workdir)

            # Minimal globals / locals.
            global_vars = {"__name__": "__main__"}
            local_vars = {}

            exec(code, global_vars, local_vars)

            if html_path.exists():
                html_content = html_path.read_text(encoding="utf-8")
            else:
                error = f"SandboxRunner: Expected {expected_html} was not created."

        except Exception as e:
            error = f"SandboxRunner error: {e}\n{traceback.format_exc()}"
        finally:
            os.chdir(old_cwd)

        return html_content, error

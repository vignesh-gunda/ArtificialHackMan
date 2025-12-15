from typing import TypedDict, List, Optional


class ValidatorState(TypedDict, total=False):
    file_path: str
    user_request: str

    columns: List[str]
    missing_columns: List[str]

    warnings: List[str]

    valid: bool
    rewritten_request: Optional[str]
    error: Optional[str]

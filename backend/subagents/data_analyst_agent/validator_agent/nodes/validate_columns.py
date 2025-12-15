from typing import List

import pandas as pd
import re

from ..state import ValidatorState


def extract_requested_columns(user_request: str) -> List[str]:
    """
    Very simple heuristic:
    - Extract words/phrases inside quotes
    - Extract capitalised words
    - Extract explicit mentions like column X, field Y
    """
    inside_quotes = re.findall(r'"(.*?)"', user_request) + re.findall(r"'(.*?)'", user_request)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_ ]+", user_request)

    candidates = set(inside_quotes + tokens)
    return [c.strip() for c in candidates if len(c.strip()) > 1]


def validate_columns_node(state: ValidatorState) -> ValidatorState:
    file_path = state.get("file_path")
    user_request = state.get("user_request", "")

    if not file_path:
        state["error"] = "validate_columns_node: 'file_path' is required."
        state["valid"] = False
        return state

    try:
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(file_path)
        else:
            state["error"] = "validate_columns_node: Unsupported file type; only CSV/XLS/XLSX allowed."
            state["valid"] = False
            return state
    except Exception as exc:  # noqa: BLE001
        state["error"] = f"validate_columns_node: Failed to load dataset: {exc}"
        state["valid"] = False
        return state

    cols = df.columns.tolist()
    state["columns"] = cols

    # Extract potential column references from user request
    requested = extract_requested_columns(user_request)

    # Actual missing ones
    missing = [c for c in requested if c not in cols]

    if missing:
        state["missing_columns"] = missing
        state["valid"] = False
        state["error"] = f"Invalid request. These columns do not exist: {missing}"
        state["warnings"] = [f"Columns not found: {', '.join(missing)}"]
        return state

    state["valid"] = True
    state["missing_columns"] = []
    state["warnings"] = []
    return state

from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import FunctionResult


def success(
    *_args: Any,
    match: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    expression = "success == true"
    if match:
        expression = f"({expression}) && ({match})"
    result = assess(match=expression)
    return FunctionResult(name="success", success=result.success, message=result.message)

from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import FunctionResult


def fail(
    *_args: Any,
    match: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    expression = "success == false"
    if match:
        expression = f"({expression}) && ({match})"
    result = assess(match=expression)
    return FunctionResult(name="fail", success=result.success, message=result.message)

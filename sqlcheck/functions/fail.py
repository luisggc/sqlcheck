from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import FunctionResult


def fail(
    *_args: Any,
    error_match: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    if error_match:
        expr = lambda r: (not r.success) and error_match in r.stderr
    else:
        expr = lambda r: not r.success
    result = assess(expr)
    return FunctionResult(name="fail", success=result.success, message=result.message)

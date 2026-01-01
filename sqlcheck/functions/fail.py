from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import FunctionResult


def fail(
    *_args: Any,
    error_match: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    result = assess(expect_success=False, error_match=error_match)
    return FunctionResult(name="fail", success=result.success, message=result.message)

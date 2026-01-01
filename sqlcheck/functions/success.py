from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import FunctionResult


def success(
    *_args: Any,
    **_kwargs: Any,
) -> FunctionResult:
    result = assess(lambda r: r.success)
    return FunctionResult(name="success", success=result.success, message=result.message)

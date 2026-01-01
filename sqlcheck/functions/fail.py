from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import ExecutionOutput, ExecutionStatus, FunctionResult, SQLParsed


def fail(
    sql_parsed: SQLParsed,
    status: ExecutionStatus,
    output: ExecutionOutput,
    *_args: Any,
    error_match: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    result = assess(sql_parsed, status, output, expect_success=False, error_match=error_match)
    return FunctionResult(name="fail", success=result.success, message=result.message)

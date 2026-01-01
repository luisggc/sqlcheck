from __future__ import annotations

from typing import Any

from sqlcheck.functions.assess import assess
from sqlcheck.models import ExecutionOutput, ExecutionStatus, FunctionResult, SQLParsed


def success(
    sql_parsed: SQLParsed,
    status: ExecutionStatus,
    output: ExecutionOutput,
    *_args: Any,
    **_kwargs: Any,
) -> FunctionResult:
    result = assess(sql_parsed, status, output, expect_success=True)
    return FunctionResult(name="success", success=result.success, message=result.message)

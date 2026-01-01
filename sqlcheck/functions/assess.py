from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from sqlcheck.function_context import current_context
from sqlcheck.models import ExecutionOutput, ExecutionStatus, FunctionResult, SQLParsed


@dataclass(frozen=True)
class AssessContext:
    stdout: str
    stderr: str
    stdin: str
    rows: list[list[Any]]
    columns: list[str]
    data: dict[str, list[Any]]
    status: ExecutionStatus
    output: ExecutionOutput
    sql: SQLParsed
    success: bool
    returncode: int
    duration_s: float

    @property
    def strerr(self) -> str:
        return self.stderr


def assess(expr: Callable[[AssessContext], bool], *_args: Any, **_kwargs: Any) -> FunctionResult:
    context = current_context()
    output = context.output
    columns = _columns_for_output(output)
    data = _build_data(columns, output.rows)
    assess_context = AssessContext(
        stdout=output.stdout,
        stderr=output.stderr,
        stdin="",
        rows=output.rows,
        columns=columns,
        data=data,
        status=context.status,
        output=output,
        sql=context.sql_parsed,
        success=context.status.success,
        returncode=context.status.returncode,
        duration_s=context.status.duration_s,
    )
    try:
        result = expr(assess_context)
    except Exception as exc:  # pragma: no cover - unexpected user error
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Assess expression raised {exc.__class__.__name__}: {exc}",
        )
    if result:
        return FunctionResult(name="assess", success=True)
    return FunctionResult(name="assess", success=False, message="Assess expression returned false")


def _columns_for_output(output: ExecutionOutput) -> list[str]:
    columns = list(output.columns)
    if output.rows:
        max_len = max(len(row) for row in output.rows)
        if not columns:
            columns = [f"column{index + 1}" for index in range(max_len)]
        elif len(columns) < max_len:
            columns.extend(
                f"column{index + 1}" for index in range(len(columns), max_len)
            )
    return columns


def _build_data(columns: list[str], rows: list[list[Any]]) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {}
    for index, column in enumerate(columns):
        data[column] = [row[index] if index < len(row) else None for row in rows]
    return data

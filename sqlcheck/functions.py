from __future__ import annotations

import re
from typing import Any, Callable

from sqlcheck.models import ExecutionOutput, ExecutionStatus, FunctionResult, SQLParsed


FunctionType = Callable[[SQLParsed, ExecutionStatus, ExecutionOutput, Any], FunctionResult]


class FunctionRegistry:
    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., FunctionResult]] = {}

    def register(self, name: str, func: Callable[..., FunctionResult]) -> None:
        self._functions[name] = func

    def resolve(self, name: str) -> Callable[..., FunctionResult]:
        if name not in self._functions:
            raise KeyError(f"Unknown function '{name}'")
        return self._functions[name]


def success(
    sql_parsed: SQLParsed,
    status: ExecutionStatus,
    output: ExecutionOutput,
    *_args: Any,
    **_kwargs: Any,
) -> FunctionResult:
    if status.success:
        return FunctionResult(name="success", success=True)
    message = "Expected success but execution failed"
    return FunctionResult(name="success", success=False, message=message)


def fail(
    sql_parsed: SQLParsed,
    status: ExecutionStatus,
    output: ExecutionOutput,
    *_args: Any,
    error_match: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    if status.success:
        return FunctionResult(name="fail", success=False, message="Expected failure but execution succeeded")
    if error_match and not _match_text(error_match, output.stderr):
        return FunctionResult(
            name="fail",
            success=False,
            message=f"Expected error to match {error_match!r}",
        )
    return FunctionResult(name="fail", success=True)


def assess(
    sql_parsed: SQLParsed,
    status: ExecutionStatus,
    output: ExecutionOutput,
    *_args: Any,
    stdout_match: str | None = None,
    stderr_match: str | None = None,
    error_match: str | None = None,
    output_match: str | None = None,
    result_equals: Any | None = None,
    result_cell: tuple[int, int] | None = None,
    expect_success: bool | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    if expect_success is not None and status.success != expect_success:
        expectation = "success" if expect_success else "failure"
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Expected {expectation} but execution {'succeeded' if status.success else 'failed'}",
        )
    if error_match and not _match_text(error_match, output.stderr):
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Expected error to match {error_match!r}",
        )
    if stderr_match and not _match_text(stderr_match, output.stderr):
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Expected stderr to match {stderr_match!r}",
        )
    if stdout_match and not _match_text(stdout_match, output.stdout):
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Expected stdout to match {stdout_match!r}",
        )
    if output_match:
        rendered = _render_rows(output.rows)
        if not _match_text(output_match, rendered):
            return FunctionResult(
                name="assess",
                success=False,
                message=f"Expected output to match {output_match!r}",
            )
    if result_equals is not None:
        row_index, col_index = result_cell or (0, 0)
        if row_index < 0 or col_index < 0:
            return FunctionResult(
                name="assess",
                success=False,
                message="Expected result_cell to be non-negative indices",
            )
        if row_index >= len(output.rows):
            return FunctionResult(
                name="assess",
                success=False,
                message=f"Expected result row {row_index} but only {len(output.rows)} row(s) returned",
            )
        row = output.rows[row_index]
        if col_index >= len(row):
            return FunctionResult(
                name="assess",
                success=False,
                message=f"Expected result column {col_index} but row has {len(row)} column(s)",
            )
        value = row[col_index]
        if value != result_equals:
            return FunctionResult(
                name="assess",
                success=False,
                message=f"Expected result[{row_index}][{col_index}] to equal {result_equals!r}",
            )
    return FunctionResult(name="assess", success=True)


def _match_text(pattern: str, text: str) -> bool:
    if pattern.startswith("re:"):
        return re.search(pattern[3:], text) is not None
    if len(pattern) >= 2 and pattern.startswith("/") and pattern.endswith("/"):
        return re.search(pattern[1:-1], text) is not None
    return pattern in text


def _render_rows(rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    rendered_rows = []
    for row in rows:
        rendered_rows.append("\t".join(str(value) for value in row))
    return "\n".join(rendered_rows)


def default_registry() -> FunctionRegistry:
    registry = FunctionRegistry()
    registry.register("success", success)
    registry.register("fail", fail)
    registry.register("assess", assess)
    return registry

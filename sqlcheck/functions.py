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
    error_contains: str | None = None,
    error_regex: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    if status.success:
        return FunctionResult(name="fail", success=False, message="Expected failure but execution succeeded")
    combined = f"{output.stdout}\n{output.stderr}".strip()
    if error_contains and error_contains not in combined:
        return FunctionResult(
            name="fail",
            success=False,
            message=f"Expected error to contain '{error_contains}'",
        )
    if error_regex and not re.search(error_regex, combined):
        return FunctionResult(
            name="fail",
            success=False,
            message=f"Expected error to match /{error_regex}/",
        )
    return FunctionResult(name="fail", success=True)


def default_registry() -> FunctionRegistry:
    registry = FunctionRegistry()
    registry.register("success", success)
    registry.register("fail", fail)
    return registry

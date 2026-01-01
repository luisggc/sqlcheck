from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator

from sqlcheck.models import ExecutionOutput, ExecutionStatus, SQLParsed

_context: ContextVar["ExecutionContext | None"] = ContextVar(
    "sqlcheck_execution_context",
    default=None,
)


@dataclass(frozen=True)
class ExecutionContext:
    sql_parsed: SQLParsed
    status: ExecutionStatus
    output: ExecutionOutput


@contextmanager
def execution_context(
    sql_parsed: SQLParsed,
    status: ExecutionStatus,
    output: ExecutionOutput,
) -> Iterator[None]:
    token = _context.set(ExecutionContext(sql_parsed=sql_parsed, status=status, output=output))
    try:
        yield
    finally:
        _context.reset(token)


def current_context() -> ExecutionContext:
    context = _context.get()
    if context is None:
        raise RuntimeError("Function execution context is not set")
    return context

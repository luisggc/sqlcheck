from __future__ import annotations

from dataclasses import dataclass

from sqlcheck.models import ExecutionOutput, ExecutionStatus, SQLParsed


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    output: ExecutionOutput


class Adapter:
    name = "base"

    def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
        raise NotImplementedError

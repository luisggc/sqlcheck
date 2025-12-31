from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SQLStatement:
    index: int
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class SQLParsed:
    source: str
    statements: list[SQLStatement]


@dataclass(frozen=True)
class DirectiveCall:
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    raw: str


@dataclass(frozen=True)
class TestMetadata:
    name: str
    tags: list[str] = field(default_factory=list)
    serial: bool = False
    timeout: float | None = None
    retries: int = 0


@dataclass(frozen=True)
class TestCase:
    path: Path
    sql_parsed: SQLParsed
    directives: list[DirectiveCall]
    metadata: TestMetadata


@dataclass(frozen=True)
class ExecutionStatus:
    success: bool
    returncode: int
    duration_s: float


@dataclass(frozen=True)
class ExecutionOutput:
    stdout: str
    stderr: str


@dataclass(frozen=True)
class FunctionResult:
    name: str
    success: bool
    message: str | None = None


@dataclass(frozen=True)
class TestResult:
    case: TestCase
    status: ExecutionStatus
    output: ExecutionOutput
    function_results: list[FunctionResult]

    @property
    def success(self) -> bool:
        return all(result.success for result in self.function_results)

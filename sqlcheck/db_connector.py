from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterator

from sqlcheck.models import ExecutionOutput, ExecutionStatus, SQLParsed


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    output: ExecutionOutput


@dataclass(frozen=True)
class DBSession:
    execute: Callable[[SQLParsed, float | None], ExecutionResult]


class DBConnector:
    name = "base"

    def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
        raise NotImplementedError

    @contextmanager
    def open_session(self) -> Iterator[DBSession]:
        yield DBSession(self.execute)


class CommandDBConnector(DBConnector):
    pass


from sqlcheck.connectors.sqlalchemy import SQLAlchemyConnector

__all__ = [
    "CommandDBConnector",
    "DBConnector",
    "DBSession",
    "ExecutionResult",
    "SQLAlchemyConnector",
]

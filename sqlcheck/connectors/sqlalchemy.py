from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.exc import NoSuchModuleError, SQLAlchemyError

from sqlcheck.db_connector import CommandDBConnector, DBSession, ExecutionResult
from sqlcheck.models import ExecutionOutput, ExecutionStatus, SQLParsed


class SQLAlchemyConnector(CommandDBConnector):
    name = "sqlalchemy"

    def __init__(self, connection_uri: str) -> None:
        self.connection_uri = connection_uri
        try:
            self.engine = create_engine(connection_uri)
        except NoSuchModuleError as exc:
            dialect = _dialect_from_uri(connection_uri)
            hint = _driver_hint(dialect)
            message = (
                f"Missing SQLAlchemy driver for '{dialect}'. {hint} "
                f"Original error: {exc}"
            )
            raise ValueError(message) from exc

    def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
        with self.engine.connect() as connection:
            return self._execute_with_connection(connection, sql_parsed, timeout)

    @contextmanager
    def open_session(self) -> Iterator[DBSession]:
        with self.engine.connect() as connection:
            def _execute(sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                return self._execute_with_connection(connection, sql_parsed, timeout)

            yield DBSession(_execute)

    def _execute_with_connection(
        self,
        connection: object,
        sql_parsed: SQLParsed,
        timeout: float | None = None,
    ) -> ExecutionResult:
        start = time.perf_counter()
        stdout = ""
        stderr = ""
        rows: list[list[object]] = []
        returncode = 0
        success = True
        try:
            exec_connection = connection
            if timeout is not None:
                exec_connection = connection.execution_options(timeout=timeout)
            with exec_connection.begin():
                statements = sql_parsed.statements
                if not statements:
                    statements = []
                for statement in statements or []:
                    result = exec_connection.exec_driver_sql(statement.text)
                    if result.returns_rows:
                        rows = [list(row) for row in result.fetchall()]
                if not statements and sql_parsed.source.strip():
                    result = exec_connection.exec_driver_sql(sql_parsed.source)
                    if result.returns_rows:
                        rows = [list(row) for row in result.fetchall()]
        except SQLAlchemyError as exc:
            success = False
            returncode = 1
            stderr = str(exc)
        duration = time.perf_counter() - start
        status = ExecutionStatus(success=success, returncode=returncode, duration_s=duration)
        output = ExecutionOutput(stdout=stdout, stderr=stderr, rows=rows)
        return ExecutionResult(status=status, output=output)


def _dialect_from_uri(connection_uri: str) -> str:
    scheme = urlparse(connection_uri).scheme
    return scheme.split("+", maxsplit=1)[0] if scheme else "unknown"


def _driver_hint(dialect: str) -> str:
    hints = {
        "snowflake": "Install the optional dependency with: pip install sqlcheck[snowflake]",
        "duckdb": "Install the optional dependency with: pip install sqlcheck[duckdb]",
        "postgresql": "Install the optional dependency with: pip install sqlcheck[postgres]",
        "mysql": "Install the optional dependency with: pip install sqlcheck[mysql]",
        "databricks": "Install the optional dependency with: pip install sqlcheck[databricks]",
    }
    message = hints.get(
        dialect,
        "Install the database-specific SQLAlchemy dialect/driver for this URI.",
    )
    return f"{message} See https://docs.sqlalchemy.org/en/20/dialects/ for details."

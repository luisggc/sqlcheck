from __future__ import annotations

import time

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from sqlcheck.adapters.base import Adapter, ExecutionResult
from sqlcheck.models import ExecutionOutput, ExecutionStatus, SQLParsed


class SQLAlchemyAdapter(Adapter):
    name = "sqlalchemy"

    def __init__(self, connection_uri: str) -> None:
        self.connection_uri = connection_uri
        self.engine = create_engine(connection_uri)

    def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
        start = time.perf_counter()
        stdout = ""
        stderr = ""
        returncode = 0
        success = True
        try:
            with self.engine.connect() as connection:
                if timeout is not None:
                    connection = connection.execution_options(timeout=timeout)
                with connection.begin():
                    statements = sql_parsed.statements
                    if not statements:
                        statements = []
                    for statement in statements or []:
                        connection.exec_driver_sql(statement.text)
                    if not statements and sql_parsed.source.strip():
                        connection.exec_driver_sql(sql_parsed.source)
        except SQLAlchemyError as exc:
            success = False
            returncode = 1
            stderr = str(exc)
        duration = time.perf_counter() - start
        status = ExecutionStatus(success=success, returncode=returncode, duration_s=duration)
        output = ExecutionOutput(stdout=stdout, stderr=stderr)
        return ExecutionResult(status=status, output=output)

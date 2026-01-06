from __future__ import annotations

import concurrent.futures
import time
from typing import Iterable

from sqlcheck.db import DBConnection, DBConnectionError
from sqlcheck.function_context import execution_context
from sqlcheck.function_registry import FunctionRegistry
from sqlcheck.models import (
    ExecutionOutput,
    ExecutionResult,
    ExecutionStatus,
    FunctionResult,
    SQLParsed,
    TestCase,
    TestResult,
)


def run_test_case(
    case: TestCase,
    connection_id: str,
    registry: FunctionRegistry,
) -> TestResult:
    execution: ExecutionResult | None = None
    function_results: list[FunctionResult] = []
    with DBConnection(connection_id) as dbc:
        for segment in case.segments:
            for attempt in range(case.metadata.retries + 1):
                execution = _execute_segment(dbc, segment.sql_parsed, case.metadata.timeout)
                if execution.status.success or attempt >= case.metadata.retries:
                    break
            if execution is None:
                raise RuntimeError("Execution never started")
            status = execution.status
            output = execution.output
            exit_on_failure = segment.directive.kwargs.get("exit_on_failure", True)
            func = registry.resolve(segment.directive.name)
            kwargs = {
                key: value
                for key, value in segment.directive.kwargs.items()
                if key != "exit_on_failure"
            }
            with execution_context(segment.sql_parsed, status, output):
                result = func(*segment.directive.args, **kwargs)
            function_results.append(result)
            if exit_on_failure and not result.success:
                break
    if execution is None:
        raise RuntimeError("Execution never started")
    return TestResult(
        case=case,
        status=execution.status,
        output=execution.output,
        function_results=function_results,
    )


def _format_query_output(rows: list[list[object]], columns: list[str] | None) -> str:
    """Format query results as newline-separated values for stdout."""
    if not columns:
        return ""

    parts = columns[:]
    for row in rows:
        parts.extend(str(val) if val is not None else "NULL" for val in row)

    return "\n".join(parts)


def _execute_segment(dbc: DBConnection, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
    """Execute SQL using DBConnection and convert to ExecutionResult."""
    start = time.perf_counter()
    stdout = ""
    stderr = ""
    rows: list[list[object]] = []
    returncode = 0
    success = True

    try:
        # Execute each statement individually (like old SQLAlchemyConnector)
        statements = sql_parsed.statements
        if not statements:
            statements = []

        for statement in statements or []:
            result = dbc.query(statement.text, fetch="auto", include_columns=True)
            if result is not None:
                result_rows, columns = result
                rows = [list(row) for row in result_rows]
                stdout = _format_query_output(rows, columns)

        # Handle case where no statements but source exists
        if not statements and sql_parsed.source.strip():
            result = dbc.query(sql_parsed.source, fetch="auto", include_columns=True)
            if result is not None:
                result_rows, columns = result
                rows = [list(row) for row in result_rows]
                stdout = _format_query_output(rows, columns)

    except DBConnectionError as exc:
        success = False
        returncode = 1
        stderr = str(exc)
    except Exception as exc:
        success = False
        returncode = 1
        stderr = str(exc)

    duration = time.perf_counter() - start
    status = ExecutionStatus(success=success, returncode=returncode, duration_s=duration)
    output = ExecutionOutput(stdout=stdout, stderr=stderr, rows=rows)
    return ExecutionResult(status=status, output=output)


def run_cases(
    cases: Iterable[TestCase],
    connection_id: str,
    registry: FunctionRegistry,
    workers: int,
) -> list[TestResult]:
    parallel_cases = [case for case in cases if not case.metadata.serial]
    serial_cases = [case for case in cases if case.metadata.serial]
    results: list[TestResult] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(run_test_case, case, connection_id, registry): case
            for case in parallel_cases
        }
        for future in concurrent.futures.as_completed(future_map):
            results.append(future.result())

    for case in serial_cases:
        results.append(run_test_case(case, connection_id, registry))

    return results

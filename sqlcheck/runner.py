from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import Iterable

from sqlcheck.db_connector import DBConnector, ExecutionResult
from sqlcheck.functions import FunctionRegistry
from sqlcheck.models import (
    DirectiveCall,
    FunctionResult,
    TestCase,
    TestMetadata,
    TestResult,
)
from sqlcheck.parser import ParsedFile, parse_file, summarize_directives


def discover_files(target: Path, pattern: str) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob(pattern))


def build_test_case(path: Path) -> TestCase:
    parsed: ParsedFile = parse_file(path)
    directives = parsed.directives or [DirectiveCall(name="success", args=(), kwargs={}, raw="")]
    summary = summarize_directives(directives)
    metadata = TestMetadata(
        name=summary["name"] or path.stem,
        tags=summary["tags"],
        serial=summary["serial"],
        timeout=summary["timeout"],
        retries=summary["retries"],
    )
    return TestCase(path=path, sql_parsed=parsed.sql_parsed, directives=directives, metadata=metadata)


def run_test_case(case: TestCase, adapter: DBConnector, registry: FunctionRegistry) -> TestResult:
    execution: ExecutionResult | None = None
    for attempt in range(case.metadata.retries + 1):
        execution = adapter.execute(case.sql_parsed, timeout=case.metadata.timeout)
        if execution.status.success or attempt >= case.metadata.retries:
            break
    if execution is None:
        raise RuntimeError("Execution never started")
    status = execution.status
    output = execution.output
    function_results: list[FunctionResult] = []
    for directive in case.directives:
        func = registry.resolve(directive.name)
        result = func(case.sql_parsed, status, output, *directive.args, **directive.kwargs)
        function_results.append(result)
    return TestResult(case=case, status=status, output=output, function_results=function_results)


def run_cases(
    cases: Iterable[TestCase],
    adapter: DBConnector,
    registry: FunctionRegistry,
    workers: int,
) -> list[TestResult]:
    parallel_cases = [case for case in cases if not case.metadata.serial]
    serial_cases = [case for case in cases if case.metadata.serial]
    results: list[TestResult] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(run_test_case, case, adapter, registry): case for case in parallel_cases
        }
        for future in concurrent.futures.as_completed(future_map):
            results.append(future.result())

    for case in serial_cases:
        results.append(run_test_case(case, adapter, registry))

    return results

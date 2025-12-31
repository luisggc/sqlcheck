from __future__ import annotations

import os
from pathlib import Path

import typer

from sqlcheck.adapters.duckdb import DuckDBAdapter
from sqlcheck.models import TestCase, TestResult
from sqlcheck.runner import build_test_case, discover_files


def discover_cases(target: Path, pattern: str) -> list[TestCase]:
    paths = discover_files(target, pattern)
    if not paths:
        print("No test files found.")
        raise typer.Exit(code=1)
    return [build_test_case(path) for path in paths]


def build_adapter(engine: str, engine_args: list[str] | None) -> DuckDBAdapter:
    if engine == "duckdb":
        command_template = os.getenv("SQLCHECK_ENGINE_COMMAND")
        return DuckDBAdapter(engine_args=engine_args, command_template=command_template)
    raise ValueError(f"Unsupported engine: {engine}")


def render_result(result: TestResult) -> str:
    lines = [f"{result.case.metadata.name} [{result.case.path}]"]
    if result.success:
        lines.append("  PASS")
    else:
        lines.append("  FAIL")
        for func_result in result.function_results:
            if not func_result.success:
                message = func_result.message or "Expectation failed"
                lines.append(f"    - {func_result.name}: {message}")
        if result.output.stderr:
            lines.append("  STDERR:")
            lines.extend(f"    {line}" for line in result.output.stderr.splitlines())
        if result.output.stdout:
            lines.append("  STDOUT:")
            lines.extend(f"    {line}" for line in result.output.stdout.splitlines())
    return "\n".join(lines)

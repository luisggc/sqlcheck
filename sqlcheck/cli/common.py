from __future__ import annotations

import os
import re
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sqlcheck.adapters.sqlalchemy import SQLAlchemyAdapter
from sqlcheck.db_connector import DBConnector
from sqlcheck.models import TestCase, TestResult
from sqlcheck.runner import build_test_case, discover_files


def discover_cases(target: Path, pattern: str) -> list[TestCase]:
    paths = discover_files(target, pattern)
    if not paths:
        print("No test files found.")
        raise typer.Exit(code=1)
    return [build_test_case(path) for path in paths]


def _connection_env_var(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    return f"SQLCHECK_CONN_{slug}"


def resolve_connection_uri(name: str) -> str:
    env_var = _connection_env_var(name)
    value = os.getenv(env_var)
    if not value:
        raise ValueError(f"Missing connection URI. Set {env_var}.")
    return value


def build_adapter(connection: str) -> DBConnector:
    connection_uri = resolve_connection_uri(connection)
    return SQLAlchemyAdapter(connection_uri=connection_uri)


def print_results(results: list[TestResult], engine: str | None = None) -> None:
    total = len(results)
    failures = [result for result in results if not result.success]
    passed = total - len(failures)
    console = Console()

    header = "SQLCheck"
    if engine:
        header += f" ({engine})"
    header += f" — {total} tests, {passed} passed"
    if failures:
        header += f", {len(failures)} failed"

    if failures:
        console.print("[bold]Failures:[/bold]")
        for result in failures:
            console.print(
                f"[red]FAIL[/red] {result.case.metadata.name}  [dim]{result.case.path}[/dim]"
            )
            for func_result in result.function_results:
                if not func_result.success:
                    message = func_result.message or "Expectation failed"
                    console.print(f"  {message}")
            if result.output.stderr:
                console.print(
                    Panel(
                        result.output.stderr.strip(),
                        title="STDERR",
                        border_style="red",
                    )
                )
            if result.output.stdout:
                console.print(
                    Panel(
                        result.output.stdout.strip(),
                        title="STDOUT",
                        border_style="yellow",
                    )
                )
        console.print()

    table = Table(box=box.ASCII, show_header=True, header_style="bold")
    table.add_column("STATUS", style="bold")
    table.add_column("TEST")
    table.add_column("DURATION", justify="right")
    table.add_column("PATH")

    for result in results:
        duration = f"{result.status.duration_s:.2f}s"
        status = "PASS" if result.success else "FAIL"
        status_style = "green" if result.success else "red"
        table.add_row(
            f"[{status_style}]{status}[/{status_style}]",
            result.case.metadata.name,
            duration,
            str(result.case.path),
        )

    console.print(table)
    console.print()
    console.print(f"[bold]{header}[/bold]")

from __future__ import annotations

from pathlib import Path

import typer

from sqlcheck.cli.common import build_adapter, discover_cases, print_results
from sqlcheck.functions import default_registry
from sqlcheck.plugins import load_plugins
from sqlcheck.reports import write_json, write_junit, write_plan
from sqlcheck.runner import run_cases


def run(
    target: Path = typer.Argument(..., help="Target file or directory to scan"),
    pattern: str = typer.Option(
        "**/*.sql", help="Glob pattern for test discovery (default: **/*.sql)"
    ),
    workers: int = typer.Option(5, help="Number of worker threads"),
    connection: str = typer.Option(
        ...,
        "--connection",
        "-c",
        help="Connection name for SQLCHECK_CONN_<NAME> environment lookup",
    ),
    json_path: Path | None = typer.Option(
        None, "--json", help="Write JSON report to path"
    ),
    junit_path: Path | None = typer.Option(
        None, "--junit", help="Write JUnit XML report to path"
    ),
    plan_dir: Path | None = typer.Option(
        None, "--plan-dir", help="Write per-test plan JSON files to this directory"
    ),
    plugin: list[str] | None = typer.Option(
        None, "--plugin", help="Plugin module path to load (can be repeated)"
    ),
) -> None:
    cases = discover_cases(target, pattern)

    registry = default_registry()
    if plugin:
        load_plugins(plugin, registry)

    adapter = build_adapter(connection)

    results = run_cases(cases, adapter, registry, workers=workers)

    print_results(results, engine=connection)

    if json_path:
        write_json(results, json_path)
    if junit_path:
        write_junit(results, junit_path)
    if plan_dir:
        plan_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            relative_name = str(result.case.path).replace("/", "__").replace("\\", "__")
            plan_path = plan_dir / f"{relative_name}.plan.json"
            write_plan(result, plan_path)

    failures = [result for result in results if not result.success]
    if failures:
        raise typer.Exit(code=1)

from __future__ import annotations

from pathlib import Path

import typer

from sqlcheck.cli.common import build_adapter, discover_cases, render_result
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
    engine: str = typer.Option("duckdb", help="Execution engine adapter"),
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
    engine_args: list[str] | None = typer.Option(
        None, "--engine-arg", help="Extra args for the engine command (repeatable)"
    ),
) -> None:
    cases = discover_cases(target, pattern)

    registry = default_registry()
    if plugin:
        load_plugins(plugin, registry)

    adapter = build_adapter(engine, engine_args)

    results = run_cases(cases, adapter, registry, workers=workers)

    for result in results:
        print(render_result(result))

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

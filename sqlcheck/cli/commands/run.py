from __future__ import annotations

from pathlib import Path

import typer

from sqlcheck.cli.discovery import discover_cases
from sqlcheck.cli.output import print_results
from sqlcheck.function_registry import default_registry
from sqlcheck.plugins import load_plugins
from sqlcheck.reports import write_json, write_junit, write_plan
from sqlcheck.runner import run_cases


def _parse_template_vars(vars_list: list[str]) -> dict[str, str]:
    """
    Parse template variables from key=value strings.

    Args:
        vars_list: List of "key=value" strings

    Returns:
        Dictionary mapping variable names to values

    Raises:
        typer.BadParameter: If any variable is malformed
    """
    variables = {}
    for var_str in vars_list:
        if "=" not in var_str:
            raise typer.BadParameter(
                f"Invalid variable format: {var_str!r}. "
                "Expected format: key=value"
            )
        key, _, value = var_str.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            raise typer.BadParameter(
                f"Invalid variable format: {var_str!r}. "
                "Variable name cannot be empty"
            )
        if key in variables:
            raise typer.BadParameter(
                f"Duplicate variable: {key!r}"
            )
        variables[key] = value
    return variables


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
        help="Connector name for SQLCHECK_CONN_<NAME> environment lookup",
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
    vars: list[str] | None = typer.Option(
        None,
        "--vars",
        "-v",
        help="Template variables in key=value format (repeatable)",
    ),
) -> None:
    # Parse template variables
    template_vars = _parse_template_vars(vars or [])

    cases = discover_cases(target, pattern, template_vars=template_vars)

    registry = default_registry()
    if plugin:
        load_plugins(plugin, registry)

    results = run_cases(cases, connection, registry, workers=workers)

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

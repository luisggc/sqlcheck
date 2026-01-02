from __future__ import annotations

import json
from pathlib import Path

import typer

from sqlcheck.cli.discovery import discover_cases
from sqlcheck.reports import build_plan_payload, write_case_plan


def plan(
    target: Path = typer.Argument(..., help="Target file or directory to scan"),
    pattern: str = typer.Option(
        "**/*.sql", help="Glob pattern for test discovery (default: **/*.sql)"
    ),
    plan_dir: Path | None = typer.Option(
        None, "--plan-dir", help="Write per-test plan JSON files to this directory"
    ),
    json_path: Path | None = typer.Option(
        None, "--json", help="Write plan output to path"
    ),
) -> None:
    cases = discover_cases(target, pattern)
    payload = [build_plan_payload(case) for case in cases]

    if plan_dir:
        plan_dir.mkdir(parents=True, exist_ok=True)
        for case in cases:
            relative_name = str(case.path).replace("/", "__").replace("\\", "__")
            plan_path = plan_dir / f"{relative_name}.plan.json"
            write_case_plan(case, plan_path)

    output = json.dumps(payload, indent=2)
    if json_path:
        json_path.write_text(output, encoding="utf-8")
    elif not plan_dir:
        print(output)

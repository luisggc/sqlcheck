from __future__ import annotations

import json
from pathlib import Path

import typer

from sqlcheck.parser import parse_file
from sqlcheck.runner import discover_files


def parse(
    target: Path = typer.Argument(..., help="Target file or directory to scan"),
    pattern: str = typer.Option(
        "**/*.sql", help="Glob pattern for test discovery (default: **/*.sql)"
    ),
    json_path: Path | None = typer.Option(
        None, "--json", help="Write parse output to path"
    ),
) -> None:
    paths = discover_files(target, pattern)
    if not paths:
        print("No test files found.")
        raise typer.Exit(code=1)

    payload = []
    for path in paths:
        parsed = parse_file(path)
        payload.append(
            {
                "path": str(path),
                "sql_source": parsed.sql_parsed.source,
                "statements": [
                    {
                        "index": stmt.index,
                        "text": stmt.text,
                        "start": stmt.start,
                        "end": stmt.end,
                    }
                    for stmt in parsed.sql_parsed.statements
                ],
                "directives": [
                    {
                        "name": directive.name,
                        "args": directive.args,
                        "kwargs": directive.kwargs,
                        "raw": directive.raw,
                    }
                    for directive in parsed.directives
                ],
            }
        )

    output = json.dumps(payload, indent=2, default=str)
    if json_path:
        json_path.write_text(output, encoding="utf-8")
    else:
        print(output)

from __future__ import annotations

from pathlib import Path

import typer

from sqlcheck.discovery import build_test_case, discover_files
from sqlcheck.models import TestCase


def discover_cases(target: Path, pattern: str) -> list[TestCase]:
    paths = discover_files(target, pattern)
    if not paths:
        print("No test files found.")
        raise typer.Exit(code=1)
    return [build_test_case(path) for path in paths]


__all__ = ["discover_cases"]

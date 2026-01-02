from __future__ import annotations

from pathlib import Path

from sqlcheck.models import DirectiveCall, TestCase, TestMetadata
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
    return TestCase(
        path=path,
        sql_parsed=parsed.sql_parsed,
        directives=directives,
        segments=parsed.segments,
        metadata=metadata,
    )

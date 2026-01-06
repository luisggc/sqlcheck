from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from sqlcheck.models import DirectiveCall, SQLParsed, SQLSegment, SQLStatement


class DirectiveParseError(ValueError):
    pass


def _split_statements(sql: str) -> list[SQLStatement]:
    """Split SQL source into individual statements, respecting string literals."""
    statements: list[SQLStatement] = []
    buffer: list[str] = []
    start = 0
    in_single = False
    in_double = False
    escape = False

    for idx, char in enumerate(sql):
        if escape:
            buffer.append(char)
            escape = False
            continue
        if char == "\\":
            escape = True
            buffer.append(char)
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        if char == ";" and not in_single and not in_double:
            text = "".join(buffer).strip()
            if text:
                statements.append(SQLStatement(len(statements), text, start, idx))
            buffer = []
            start = idx + 1
        else:
            buffer.append(char)

    tail = "".join(buffer).strip()
    if tail:
        statements.append(SQLStatement(len(statements), tail, start, len(sql)))
    return statements


@dataclass(frozen=True)
class ParsedFile:
    sql_parsed: SQLParsed
    directives: list[DirectiveCall]
    segments: list[SQLSegment]
    template_vars: dict[str, str] = field(default_factory=dict)


def parse_file(path: Path, template_vars: dict[str, str] | None = None) -> ParsedFile:
    """
    Parse a SQL test file, extracting directives and SQL statements.

    Uses Jinja2 to render template variables and extract directive function calls.

    Args:
        path: Path to SQL file
        template_vars: Optional template variables for Jinja rendering

    Returns:
        ParsedFile containing directives, SQL, and segments

    Raises:
        DirectiveParseError: If template rendering or parsing fails
    """
    source = path.read_text(encoding="utf-8")

    # Render with Jinja, extracting both variables and directives
    from sqlcheck.template import render_template, TemplateRenderError

    try:
        rendered, directive_markers = render_template(source, template_vars)
    except TemplateRenderError as exc:
        raise DirectiveParseError(
            f"Template rendering failed for {path}: {exc}"
        ) from exc

    # Convert markers to DirectiveCall objects
    directives = [
        DirectiveCall(
            name=marker.name,
            args=marker.args,
            kwargs=marker.kwargs,
            raw=marker.raw_text
        )
        for marker in directive_markers
    ]

    # Check for deprecated config() directive
    if any(directive.name == "config" for directive in directives):
        raise DirectiveParseError(
            "config() is not supported; use exit_on_failure on directives"
        )

    # Strip directive placeholders to get clean SQL
    sql_source = _strip_directive_placeholders(rendered, directive_markers)

    # Parse SQL statements
    statements = _split_statements(sql_source)
    sql_parsed = SQLParsed(source=sql_source, statements=statements)

    # Segment SQL with directives
    segments = _segment_sql_with_markers(rendered, directive_markers, directives)

    return ParsedFile(
        sql_parsed=sql_parsed,
        directives=directives,
        segments=segments,
        template_vars=template_vars or {},
    )


def _strip_directive_placeholders(rendered: str, markers: list) -> str:
    """Remove directive placeholders from rendered SQL."""
    result = rendered
    for marker in markers:
        result = result.replace(marker.placeholder, '')
    return result.strip()


def _segment_sql_with_markers(
    rendered: str,
    markers: list,
    directives: list[DirectiveCall]
) -> list[SQLSegment]:
    """
    Pair SQL blocks with their controlling directives.

    Handles:
    - Directive BEFORE SQL (new style): {{ assess() }} SELECT 1;
    """
    if not markers:
        # No directives, create default segment with all SQL
        sql_source = _strip_directive_placeholders(rendered, [])
        if sql_source.strip():
            statements = _split_statements(sql_source)
            default_directive = DirectiveCall(name="success", args=(), kwargs={}, raw="")
            return [SQLSegment(
                sql_parsed=SQLParsed(source=sql_source, statements=statements),
                directive=default_directive
            )]
        return []

    segments: list[SQLSegment] = []
    chunks: list[str] = []
    cursor = 0

    for marker in markers:
        marker_pos = rendered.find(marker.placeholder, cursor)
        if marker_pos == -1:
            continue
        chunks.append(rendered[cursor:marker_pos])
        cursor = marker_pos + len(marker.placeholder)
    chunks.append(rendered[cursor:])

    for index, directive in enumerate(directives):
        sql_after = chunks[index + 1].strip() if index + 1 < len(chunks) else ""
        if not sql_after:
            continue
        statements = _split_statements(sql_after)
        segments.append(SQLSegment(
            sql_parsed=SQLParsed(source=sql_after, statements=statements),
            directive=directive
        ))

    return segments


def summarize_directives(directives: Iterable[DirectiveCall]) -> dict[str, Any]:
    """Extract metadata (name, tags, serial, timeout, retries) from directives."""
    summary: dict[str, Any] = {
        "serial": False,
        "timeout": None,
        "retries": 0,
        "tags": [],
        "name": None,
    }
    for directive in directives:
        if "serial" in directive.kwargs:
            summary["serial"] = summary["serial"] or bool(directive.kwargs["serial"])
        if "timeout" in directive.kwargs:
            summary["timeout"] = max(summary["timeout"] or 0, float(directive.kwargs["timeout"]))
        if "retries" in directive.kwargs:
            summary["retries"] = max(summary["retries"], int(directive.kwargs["retries"]))
        if "tags" in directive.kwargs:
            tags = directive.kwargs["tags"]
            if isinstance(tags, str):
                summary["tags"].append(tags)
            else:
                summary["tags"].extend(list(tags))
        if "name" in directive.kwargs and not summary["name"]:
            summary["name"] = str(directive.kwargs["name"])
    return summary

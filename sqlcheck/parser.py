from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from sqlcheck.models import DirectiveCall, SQLParsed, SQLSegment, SQLStatement

DIRECTIVE_PATTERN = re.compile(r"\{\{\s*(.+?)\s*\}\}", re.DOTALL)


class DirectiveParseError(ValueError):
    pass


def _split_statements(sql: str) -> list[SQLStatement]:
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


def _literal_eval(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError) as exc:
        raise DirectiveParseError(f"Unsupported literal in directive: {ast.dump(node)}") from exc


def _parse_callable(expr: ast.expr) -> tuple[str, tuple[Any, ...], dict[str, Any]]:
    if not isinstance(expr, ast.Call):
        raise DirectiveParseError("Directive must be a function call")
    func_name = _parse_func_name(expr.func)
    args = tuple(_literal_eval(arg) for arg in expr.args)
    kwargs: dict[str, Any] = {}
    for kw in expr.keywords:
        if kw.arg is None:
            raise DirectiveParseError("Directive kwargs must be explicit key=value pairs")
        kwargs[kw.arg] = _literal_eval(kw.value)
    return func_name, args, kwargs


def _parse_func_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_parse_func_name(node.value)}.{node.attr}"
    raise DirectiveParseError("Unsupported function name in directive")


def parse_directives(source: str) -> list[DirectiveCall]:
    directives: list[DirectiveCall] = []
    for match in DIRECTIVE_PATTERN.finditer(source):
        raw = match.group(0)
        inner = match.group(1)
        try:
            parsed = ast.parse(inner, mode="eval")
        except SyntaxError as exc:
            raise DirectiveParseError(f"Invalid directive syntax: {inner}") from exc
        name, args, kwargs = _parse_callable(parsed.body)
        directives.append(DirectiveCall(name=name, args=args, kwargs=kwargs, raw=raw))
    return directives


def strip_directives(source: str) -> str:
    return DIRECTIVE_PATTERN.sub("", source)


def _segment_sql(source: str, directives: list[DirectiveCall]) -> list[SQLSegment]:
    segments: list[SQLSegment] = []
    matches = list(DIRECTIVE_PATTERN.finditer(source))
    if len(matches) != len(directives):
        raise DirectiveParseError("Directive list does not match source")
    cursor = 0
    pending_directive: DirectiveCall | None = None
    pending_sql = ""

    def build_segment(directive: DirectiveCall, sql_text: str) -> None:
        sql_source = strip_directives(sql_text)
        statements = _split_statements(sql_source)
        segments.append(SQLSegment(sql_parsed=SQLParsed(source=sql_source, statements=statements), directive=directive))

    for match, directive in zip(matches, directives, strict=True):
        sql_chunk = source[cursor : match.start()]
        pending_sql += sql_chunk
        if pending_directive is not None and strip_directives(pending_sql).strip():
            build_segment(pending_directive, pending_sql)
            pending_directive = None
            pending_sql = ""
        elif pending_directive is None and strip_directives(pending_sql).strip():
            build_segment(directive, pending_sql)
            pending_sql = ""
            cursor = match.end()
            continue
        pending_directive = directive
        cursor = match.end()
    pending_sql += source[cursor:]
    if pending_directive is not None:
        build_segment(pending_directive, pending_sql)
        pending_sql = ""
    if strip_directives(pending_sql).strip():
        build_segment(
            DirectiveCall(name="success", args=(), kwargs={}, raw=""),
            pending_sql,
        )
    return segments


@dataclass(frozen=True)
class ParsedFile:
    sql_parsed: SQLParsed
    directives: list[DirectiveCall]
    segments: list[SQLSegment]


def parse_file(path: Path) -> ParsedFile:
    source = path.read_text(encoding="utf-8")
    directives = parse_directives(source)
    if any(directive.name == "config" for directive in directives):
        raise DirectiveParseError("config() is not supported; use exit_on_failure on directives")
    sql_source = strip_directives(source)
    statements = _split_statements(sql_source)
    sql_parsed = SQLParsed(source=sql_source, statements=statements)
    segments = _segment_sql(source, directives)
    return ParsedFile(sql_parsed=sql_parsed, directives=directives, segments=segments)


def summarize_directives(directives: Iterable[DirectiveCall]) -> dict[str, Any]:
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

from __future__ import annotations

from typing import Any

from cel import evaluate

from sqlcheck.function_context import current_context
from sqlcheck.models import FunctionResult


def assess(
    *_args: Any,
    match: str | None = None,
    check: str | None = None,
    **_kwargs: Any,
) -> FunctionResult:
    expression, error_message = _resolve_match_expression(match, check)
    if expression is None:
        return FunctionResult(
            name="assess",
            success=False,
            message=error_message or "Match expression is required for assess()",
        )
    if not isinstance(expression, str):
        return FunctionResult(
            name="assess",
            success=False,
            message="Match expression must be a string",
        )
    context = current_context()
    try:
        result = evaluate(expression, _build_evaluation_context(context))
    except Exception as exc:  # noqa: BLE001 - surface CEL evaluation errors
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Match expression {expression!r} failed: {exc}",
        )
    if not isinstance(result, bool):
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Match expression {expression!r} did not evaluate to a boolean",
        )
    if not result:
        return FunctionResult(
            name="assess",
            success=False,
            message=f"Match expression {expression!r} evaluated to false",
        )
    return FunctionResult(name="assess", success=True)


def _resolve_match_expression(
    match: str | None,
    check: str | None,
) -> tuple[str | None, str | None]:
    if match and check and match != check:
        return None, "Provide only one of match or check"
    return match or check, None


def _build_evaluation_context(context: Any) -> dict[str, Any]:
    status = context.status
    output = context.output
    sql_parsed = context.sql_parsed
    status_label = "success" if status.success else "fail"
    return {
        "status": status_label,
        "success": status.success,
        "returncode": status.returncode,
        "error_code": str(status.returncode),
        "duration_s": status.duration_s,
        "elapsed_ms": int(status.duration_s * 1000),
        "stdout": output.stdout,
        "stderr": output.stderr,
        "error_message": output.stderr,
        "rows": output.rows,
        "output": {
            "stdout": output.stdout,
            "stderr": output.stderr,
            "rows": output.rows,
        },
        "sql": sql_parsed.source,
        "statements": [statement.text for statement in sql_parsed.statements],
        "statement_count": len(sql_parsed.statements),
    }

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
        debug_info = _get_debug_info(expression, _build_evaluation_context(context))
        message = f"Match expression {expression!r} evaluated to false"
        if debug_info:
            message += f"\n  {debug_info}"
        return FunctionResult(
            name="assess",
            success=False,
            message=message,
        )
    return FunctionResult(name="assess", success=True)


def _resolve_match_expression(
    match: str | None,
    check: str | None,
) -> tuple[str | None, str | None]:
    if match and check and match != check:
        return None, "Provide only one of match or check"
    return match or check, None


def _get_debug_info(expression: str, eval_context: dict[str, Any]) -> str:
    """Show values of context variables that appear in the expression."""
    import re

    # Find which context variables are referenced in the expression
    relevant_vars = {}
    for var_name, var_value in eval_context.items():
        # Check if this variable appears in the expression
        if re.search(rf"\b{re.escape(var_name)}\b", expression):
            relevant_vars[var_name] = var_value

    if not relevant_vars:
        return ""

    # Format the output
    parts = []
    for var_name, var_value in relevant_vars.items():
        # Try to find the full expression with this variable (e.g., rows[0][0])
        # by looking for patterns like var_name[...][...]
        pattern = rf"{re.escape(var_name)}(?:\[[^\]]+\])*"
        matches = re.findall(pattern, expression)

        for match in matches:
            try:
                evaluated = evaluate(match, eval_context)
                parts.append(f"{match} = {evaluated!r}")
            except Exception:  # noqa: BLE001, S110
                pass

    return ", ".join(parts) if parts else ""


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

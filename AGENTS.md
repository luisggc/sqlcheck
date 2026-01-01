# AGENTS.md

## Scope
These instructions apply to the entire repository.

## Project overview
SQLCheck is a SQL test runner that parses `.sql` files with embedded expectations and executes
them through database connectors. Key modules:

- `sqlcheck/cli/` — CLI entry points and command helpers.
- `sqlcheck/runner.py` — test discovery/execution and result handling.
- `sqlcheck/db_connector.py` — base connector abstractions and execution result types.
- `sqlcheck/adapters/` — concrete connector implementations.
- `sqlcheck/models.py` — dataclasses and typed structures used across the codebase.
- `tests/` — pytest-based test suite.

## Workflow expectations
- Use `rg` for searching (avoid `ls -R` and `grep -R`).
- Prefer small, focused commits that describe the intent.
- Keep changeset minimal; do not edit unrelated files.
- Follow existing formatting and naming conventions.

## Testing
- Install dev dependencies with: `uv sync --extra dev`
- Run tests with: `uv run pytest`
- If tests are not run, state the reason in the final response.

## CLI conventions
- CLI help text should use user-facing terms such as "connector" (not "adapter").
- Any new CLI option or behavior change should be reflected in help strings.

## Connector patterns
- Base types live in `sqlcheck/db_connector.py`.
- Concrete implementations should subclass `CommandDBConnector` or `DBConnector`.
- Keep `ExecutionResult` return values consistent (status + output).

## Reporting
- When updating reports or result formats, check `tests/test_reports.py` and `sqlcheck/reports.py`
  for expected schema and update tests accordingly.

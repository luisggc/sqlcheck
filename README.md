# sqlcheck

`sqlcheck` is a lightweight CLI for validating SQL deployments in CI. It scans SQL test source
files, extracts expectation directives like `{{ success(...) }}` or `{{ fail(...) }}`, executes
the compiled SQL against a target engine, and reports per-test results. The design is database-
agnostic and built for fast, parallel execution with clear failure output.

> **Note:** The first execution engine included is DuckDB via its CLI for local testing. The
> architecture is ready for additional engines (e.g., Snowflake via `snow sql`).

## Features

- **Directive-based expectations**: `{{ success(...) }}` and `{{ fail(...) }}` directives define
  expected behavior directly inside SQL test files.
- **Deterministic parse/compile stage**: Directives are stripped to produce executable SQL plus
  structured `sql_parsed` statement metadata.
- **Parallel execution**: Run tests concurrently with a configurable worker pool (default: 5).
- **CI-friendly outputs**: Clear per-test failures, non-zero exit codes, and JSON/JUnit reports.
- **Extensible assertions**: Register custom functions via plugins.

## Installation

### From source (recommended during development)

```bash
git clone <repo-url>
cd sqlcheck
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### Prerequisites

- **Python 3.10+**
- **DuckDB CLI** (`duckdb` in your `PATH`) for local execution

## Quick start

1. Create a SQL test file (default pattern: `**/*.sqltest`):

```sql
-- tests/example.sqltest
CREATE TABLE t (id INT);
INSERT INTO t VALUES (1);
SELECT * FROM t;

{{ success(name="basic insert") }}
```

2. Run sqlcheck:

```bash
sqlcheck tests/ --pattern "**/*.sqltest" --engine duckdb
```

If any test fails, `sqlcheck` exits with a non-zero status code.

## SQLTest directives

Directives are un-commented blocks in the SQL source:

```sql
{{ success(name="my test", tags=["smoke"], timeout=30, retries=1) }}
{{ fail(error_contains="permission", error_regex="denied") }}
```

- **`success(...)`**: Asserts the SQL executed without errors.
- **`fail(...)`**: Asserts the SQL failed, optionally matching error text with
  `error_contains` and/or `error_regex`.

If no directive is provided, `sqlcheck` defaults to `success()`.

## CLI usage

```bash
sqlcheck TARGET [options]
```

**Options**

- `--pattern`: Glob for discovery (default: `**/*.sqltest`).
- `--workers`: Parallel worker count (default: 5).
- `--engine`: Execution adapter (default: `duckdb`).
- `--duckdb-db`: DuckDB database path (default: `:memory:`).
- `--json`: Write JSON report to path.
- `--junit`: Write JUnit XML report to path.
- `--plan-dir`: Write per-test plan JSON files to a directory.
- `--plugin`: Load custom expectation functions (repeatable).

## Plugin functions

Create a Python module with a `register(registry)` function:

```python
# my_plugin.py
from sqlcheck.models import FunctionResult


def register(registry):
    def assert_rows(sql_parsed, status, output, min_rows=1, **kwargs):
        # Implement logic here based on stdout/stderr or engine-specific output
        return FunctionResult(name="assert_rows", success=True)

    registry.register("assert_rows", assert_rows)
```

Run with:

```bash
sqlcheck tests/ --plugin my_plugin
```

## Reports

- **JSON**: machine-readable summary of each test and its results.
- **JUnit XML**: CI-friendly test report format.
- **Plan files**: per-test JSON containing statement splits, directives, and metadata.

## Running tests

```bash
python -m unittest discover -s tests
```

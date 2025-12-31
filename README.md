# SQLCheck

SQLCheck turns SQL files into CI-grade tests with inline expectations. It scans SQL test source
files, extracts directives like `{{ success(...) }}` or `{{ fail(...) }}`, executes the compiled
SQL against a target engine, and reports per-test results with fast, parallel execution.

> **Note:** The first execution engine included is DuckDB via its CLI for local testing. The
> architecture is ready for additional engines (for example, Snowflake via `snow sql`).

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
uv sync
source .venv/bin/activate
```

`uv sync` creates `.venv` by default and installs the `sqlcheck` entry point into it.

### Prerequisites

- **Python 3.10+**
- **DuckDB CLI** (`duckdb` in your `PATH`) for local execution

### Install DuckDB CLI

```bash
curl https://install.duckdb.org | sh
```

## Quick start

1. Create a SQL test file (default pattern: `**/*.sql`):

```sql
-- tests/example.sql
{{ success(name="basic insert") }}

CREATE TABLE t (id INT);
INSERT INTO t VALUES (1);
SELECT * FROM t;
```

2. Run sqlcheck:

```bash
sqlcheck run tests/ --pattern "**/*.sql" --engine duckdb
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

If no directive is provided, `sqlcheck` defaults to `success()`. The `name` parameter is optional;
when omitted, the test name defaults to the file path.

## CLI usage

```bash
sqlcheck run TARGET [options]
```

**Options**

- `--pattern`: Glob for discovery (default: `**/*.sql`).
- `--workers`: Parallel worker count (default: 5).
- `--engine`: Execution adapter (default: `duckdb`).
- `--engine-arg`: Extra args for the engine command (repeatable).
- `--json`: Write JSON report to path.
- `--junit`: Write JUnit XML report to path.
- `--plan-dir`: Write per-test plan JSON files to a directory.
- `--plugin`: Load custom expectation functions (repeatable).

### Snowflake example

SQLCheck uses DuckDB by default, but you can point it at `snow sql` with a command template:

```bash
SQLCHECK_ENGINE_COMMAND="snow sql -f {file_path}" \
  sqlcheck run tests/
```

## Reports

- **JSON**: machine-readable summary of each test and its results.
- **JUnit XML**: CI-friendly test report format.
- **Plan files**: per-test JSON containing statement splits, directives, and metadata.

## Contributing

### Development setup

```bash
uv sync --extra dev
```

### Plugin functions

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
sqlcheck run tests/ --plugin my_plugin
```

### Running tests

```bash
python -m unittest discover -s tests
```

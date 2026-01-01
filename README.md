# SQLCheck

SQLCheck turns SQL files into CI-grade tests with inline expectations. It scans SQL test source
files, extracts directives like `{{ assess(...) }}`, executes the compiled
SQL against a target database using SQLAlchemy, and reports per-test results with fast, parallel
execution.

## Features

- **Directive-based expectations**: `{{ assess(...) }}` directives define expected behavior
  directly inside SQL test files.
- **Deterministic parse/compile stage**: Directives are stripped to produce executable SQL plus
  structured `sql_parsed` statement metadata.
- **Parallel execution**: Run tests concurrently with a configurable worker pool (default: 5).
- **CI-friendly outputs**: Clear per-test failures, non-zero exit codes, and JSON/JUnit reports.
- **Extensible assertions**: Register custom functions via plugins.

## Installation

### From PyPI

```bash
pip install pysqlcheck
```

SQLAlchemy requires a database-specific driver (dialect) package. Install the one for your
database, for example:

```bash
# PostgreSQL
pip install pysqlcheck[postgres]

# MySQL
pip install pysqlcheck[mysql]

# Snowflake
pip install pysqlcheck[snowflake]
```

Common optional extras (mirrors popular SQLAlchemy dialects) include:

```bash
# Databricks
pip install pysqlcheck[databricks]

# DuckDB
pip install pysqlcheck[duckdb]

# Microsoft SQL Server (ODBC)
pip install pysqlcheck[mssql]

# Oracle
pip install pysqlcheck[oracle]

# Everything above
pip install pysqlcheck[all]
```

If you need a different database dialect, install the SQLAlchemy driver for it directly. See
https://docs.sqlalchemy.org/en/20/dialects/ for the full list and driver guidance.

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
- **SQLAlchemy-compatible database connection**

## Quick start

1. Create a SQL test file (default pattern: `**/*.sql`):

```sql
-- tests/example.sql
{{ assess(lambda r: r.success, name="basic insert") }}

CREATE TABLE t (id INT);
INSERT INTO t VALUES (1);
SELECT * FROM t;
```

2. Run sqlcheck with a connection name:

```bash
# Provide a connection URI via environment variable
export SQLCHECK_CONN_DEV="sqlite:///tmp/sqlcheck.db"
sqlcheck run tests/ --connection dev

# Short flag works too
sqlcheck run tests/ -c dev
```

If any test fails, `sqlcheck` exits with a non-zero status code.

## SQLTest directives

Directives are un-commented blocks in the SQL source:

```sql
{{ assess(lambda r: r.success, name="my test", tags=["smoke"], timeout=30, retries=1) }}
{{ assess(lambda r: (not r.success) and "permission" in r.stderr.lower()) }}
{{ assess(lambda r: r.stdout == "ok" and "warning" in r.stderr) }}
{{ assess(lambda r: r.data["column1"][0] == 0) }}
```

- **`assess(...)`**: Evaluates a lambda against the execution context. The lambda receives a
  context object with `stdout`, `stderr`, `rows`, `columns`, `data`, `success`, `returncode`,
  `duration_s`, and the full `status`, `output`, and `sql` fields.

If no directive is provided, `sqlcheck` defaults to `assess(lambda r: r.success)`. The `name`
parameter is optional; when omitted, the test name defaults to the file path.

## CLI usage

```bash
sqlcheck run TARGET [options]
```

**Options**

- `--pattern`: Glob for discovery (default: `**/*.sql`).
- `--workers`: Parallel worker count (default: 5).
- `--connection`, `-c`: Connection name for `SQLCHECK_CONN_<NAME>` lookup.
- `--json`: Write JSON report to path.
- `--junit`: Write JUnit XML report to path.
- `--plan-dir`: Write per-test plan JSON files to a directory.
- `--plugin`: Load custom expectation functions (repeatable).

## Connection configuration

SQLCheck resolves connection URIs from environment variables. For a connection name like
`snowflake_prod`, SQLCheck looks up `SQLCHECK_CONN_SNOWFLAKE_PROD`.

```bash
export SQLCHECK_CONN_SNOWFLAKE_PROD="snowflake://user:pass@account/db/schema"
sqlcheck run tests/ --connection snowflake_prod
```

Connection names are uppercased and any non-alphanumeric characters are converted to underscores
before the lookup.

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
from sqlcheck.function_context import current_context
from sqlcheck.models import FunctionResult


def register(registry):
    def assert_rows(min_rows=1, **kwargs):
        context = current_context()
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

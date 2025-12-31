# SQLCheck

SQLCheck turns SQL files into CI-grade tests with inline expectations. It scans SQL test source
files, extracts directives like `{{ success(...) }}` or `{{ fail(...) }}`, executes the compiled
SQL against a target engine, and reports per-test results with fast, parallel execution.

> **Note:** SQLCheck supports DuckDB and Snowflake via built-in adapters (`--engine duckdb` or
> `--engine snowflake`). For other databases, use the `base` engine with a custom command
> template via `SQLCHECK_ENGINE_COMMAND`.

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
- **SQL execution engine** (optional): DuckDB CLI, Snowflake CLI, or custom command via `SQLCHECK_ENGINE_COMMAND`

### Install DuckDB CLI (optional)

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

2. Run sqlcheck with your preferred engine:

```bash
# Using DuckDB (recommended for getting started)
sqlcheck run tests/ --engine duckdb

# Using Snowflake with connection profile
sqlcheck run tests/ --engine snowflake --engine-arg "-c dev"

# Using a custom engine command
SQLCHECK_ENGINE_COMMAND="psql -f {file_path}" sqlcheck run tests/
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
- `--engine`: Execution adapter (default: `base`).
- `--engine-arg`: Extra args for the engine command (supports shell-style quoting, repeatable).
- `--json`: Write JSON report to path.
- `--junit`: Write JUnit XML report to path.
- `--plan-dir`: Write per-test plan JSON files to a directory.
- `--plugin`: Load custom expectation functions (repeatable).

## Engine configuration

SQLCheck supports multiple SQL engines through built-in adapters and custom command templates.

### Built-in adapters

Use the `--engine` parameter to select a built-in adapter:

```bash
# DuckDB (in-memory database)
sqlcheck run tests/ --engine duckdb

# DuckDB with a persistent database file
sqlcheck run tests/ --engine duckdb --engine-arg /path/to/database.db

# Snowflake (uses snow CLI)
sqlcheck run tests/ --engine snowflake --engine-arg "-c dev"
```

**Available engines:**
- `duckdb` - DuckDB CLI (requires `duckdb` in PATH)
- `snowflake` - Snowflake CLI (requires `snow` in PATH)
- `base` - Custom command via `SQLCHECK_ENGINE_COMMAND` (default)

### Custom engines with SQLCHECK_ENGINE_COMMAND

For engines without a built-in adapter, use the `base` engine with a custom command template:

```bash
# Using environment variable
SQLCHECK_ENGINE_COMMAND="psql -f {file_path}" sqlcheck run tests/

# With inline SQL (using stdin)
SQLCHECK_ENGINE_COMMAND="mysql -u root -p" sqlcheck run tests/

# With SQL as command argument
SQLCHECK_ENGINE_COMMAND="clickhouse-client --query {sql}" sqlcheck run tests/
```

**Template variables:**
- `{file_path}` - Path to a temporary file containing the SQL
- `{sql}` - The SQL query as a command-line argument (properly quoted)
- `{engine_args}` - Additional arguments passed via `--engine-arg` flags

**Examples with template variables:**

```bash
# Databricks with engine args (each arg passed separately)
SQLCHECK_ENGINE_COMMAND="databricks sql --warehouse-id {engine_args}" \
  sqlcheck run tests/ --engine-arg "abc123"

# Snowflake with multiple args
SQLCHECK_ENGINE_COMMAND="snow sql -c {engine_args} -f {file_path}" \
  sqlcheck run tests/ --engine-arg "dev"

# PostgreSQL with multiple connection parameters
SQLCHECK_ENGINE_COMMAND="psql {engine_args} -f {file_path}" \
  sqlcheck run tests/ --engine-arg "-h localhost -d mydb"

# Using inline SQL
SQLCHECK_ENGINE_COMMAND="psql -h localhost -d mydb -c {sql}" \
  sqlcheck run tests/
```

**How it works:**
- If `{file_path}` is used, SQLCheck creates a temporary `.sql` file
- If `{sql}` is used, SQL is passed as a command argument
- If neither is used, SQL is piped to stdin (default behavior)
- `{engine_args}` is replaced with all `--engine-arg` values joined by spaces
- `--engine-arg` supports shell-style quoting, so you can write:
  - `--engine-arg "-c dev"` (simple case, parsed into two args: `-c` and `dev`)
  - `--engine-arg '-h localhost -d "my database"'` (with quoted strings containing spaces)
  - `--engine-arg "-c" --engine-arg "dev"` (or use multiple flags if you prefer)

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

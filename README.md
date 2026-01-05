# SQLCheck

SQLCheck turns SQL files into CI-grade tests with inline expectations. It scans SQL test source
files, extracts directives like `{{ success(...) }}` or `{{ fail(...) }}`, executes the compiled
SQL against a target database using SQLAlchemy, and reports per-test results with fast, parallel
execution.

## Features

- **Directive-based expectations**: `{{ success(...) }}` and `{{ fail(...) }}` directives define
  expected behavior directly inside SQL test files.
- **Deterministic parse/compile stage**: Directives are stripped to produce executable SQL plus
  structured `sql_parsed` statement metadata.
- **Parallel execution**: Run tests concurrently with a configurable worker pool (default: 5).
- **CI-friendly outputs**: Clear per-test failures, non-zero exit codes, and JSON/JUnit reports.
- **Extensible assertions**: Register custom functions via plugins.

## Installation

### From PyPI

```bash
uv tool install pysqlcheck
```

SQLAlchemy requires a database-specific driver (dialect) package. Install the one for your
database, for example:

```bash
# Snowflake
uv tool install pysqlcheck[snowflake]
```

Common optional extras (mirrors popular SQLAlchemy dialects) include: databricks, mssql, duckdb, oracle...

If you need a different database dialect, install the SQLAlchemy driver for it directly. See
https://docs.sqlalchemy.org/en/20/dialects/ for the full list and driver guidance.

### From GitHub (recommended)

Install the latest version directly from GitHub using `uv`:

```bash
uv tool install git+https://github.com/luisggc/sqlcheck
```

To install from a specific branch:

```bash
uv tool install git+https://github.com/luisggc/sqlcheck@branch-name
```

### From source (for development)

```bash
git clone <repo-url>
cd sqlcheck
uv sync
source .venv/bin/activate
```

`uv sync` creates `.venv` by default and installs the `sqlcheck` entry point into it.

### Prerequisites

- **Python 3.11+**
- **SQLAlchemy-compatible database connection**

## Quick start

1. Create a SQL test file (default pattern: `**/*.sql`):

```sql
-- tests/example.sql
{{ success(name="basic insert") }}

CREATE TABLE t (id INT);
INSERT INTO t VALUES (1);
SELECT * FROM t;
```

2. Run sqlcheck with a database connection:

```bash
# Option 1: Set a default connection (no -c flag needed)
export SQLCHECK_CONN_DEFAULT="sqlite:///tmp/sqlcheck.db"
sqlcheck run tests/

# Option 2: Use a named connection
export SQLCHECK_CONN_DEV="sqlite:///tmp/sqlcheck.db"
sqlcheck run tests/ --connection dev

# Short flag works too
sqlcheck run tests/ -c dev

# Option 3: Pass a direct URL
sqlcheck run tests/ -c "sqlite:///tmp/sqlcheck.db"
```

If any test fails, `sqlcheck` exits with a non-zero status code.

See [Connection configuration](#connection-configuration) for more options including YAML files.

## SQLTest directives

Directives are un-commented blocks in the SQL source:

```sql
{{ success(name="my test", tags=["smoke"], timeout=30, retries=1) }}
{{ fail(match="'permission denied' in error_message") }}
{{ assess(match="stdout == 'ok' && rows.size() == 1") }}
{{ assess(match="status == 'fail' && 'type error' in error_message") }}
{{ assess(check="stdout.matches('^ok') && returncode == 0") }}
```

- **`success(...)`**: Asserts the SQL executed without errors. Optional `match` expressions add
  further checks.
- **`fail(...)`**: Asserts the SQL failed. Optional `match` expressions add further checks.
- **`assess(...)`**: Evaluates a CEL (Common Expression Language) expression supplied via the
  required `match` (or `check`) argument. The expression must evaluate to `true`.

CEL variables available to `match`:

- `status`: `"success"` or `"fail"`.
- `success`: Boolean success flag.
- `returncode`: Integer return code.
- `error_code`: String version of the return code.
- `duration_s`: Execution duration in seconds.
- `elapsed_ms`: Execution duration in milliseconds.
- `stdout`: Captured stdout.
- `stderr`: Captured stderr.
- `error_message`: Alias for stderr.
- `rows`: Query result rows as a list of lists.
- `output`: Nested object with `stdout`, `stderr`, and `rows`.
- `sql`: Full SQL source (directives stripped).
- `statements`: List of parsed SQL statements.
- `statement_count`: Count of parsed SQL statements.

Common CEL expressions:

- Contains text: `stdout.contains("warning")`
- Regex match: `stdout.matches("^ok")` or `matches(stdout, "^ok")`
- Comparisons: `returncode != 0`, `statement_count >= 1`
- Row assertions: `rows.size() == 1`, `rows[0][0] > 0`
- Status checks: `status == "success"`, `success == true`

If no directive is provided, `sqlcheck` defaults to `success()`. The `name` parameter is optional;
when omitted, the test name defaults to the file path.

## CLI usage

```bash
sqlcheck run TARGET [options]
```

### Options

- `--pattern`: Glob for discovery (default: `**/*.sql`).
- `--workers`: Parallel worker count (default: 5).
- `--connection`, `-c`: Connection name for `SQLCHECK_CONN_<NAME>` lookup.
- `--json`: Write JSON report to path.
- `--junit`: Write JUnit XML report to path.
- `--plan-dir`: Write per-test plan JSON files to a directory.
- `--plugin`: Load custom expectation functions (repeatable).

## Connection configuration

SQLCheck resolves connection URIs in this order (first match wins):

1. Default connection (when `-c` is omitted)
2. Direct URL (if contains "://")
3. Environment variables
4. YAML configuration files

### Environment variables

SQLCheck supports two environment variable prefixes:

- `SQLCHECK_CONN_{NAME}` — SQLAlchemy URL for a named connection
- `DTK_CONN_{NAME}` — Alternative prefix for compatibility
- `SQLCHECK_CONN_DEFAULT` — Default connection used when `-c` is omitted
- `DTK_CONN_DEFAULT` — Alternative default connection

Connection names are normalized by converting to uppercase and replacing non-alphanumeric
characters with underscores.

**Example:**

```bash
export SQLCHECK_CONN_DEFAULT="sqlite:///tmp/sqlcheck.db"
export SQLCHECK_CONN_SNOWFLAKE_PROD="snowflake://user:pass@account/db/schema"

# Uses default connection
sqlcheck run tests/

# Uses snowflake_prod connection
sqlcheck run tests/ --connection snowflake_prod
```

### YAML configuration file (optional)

For better organization and to avoid exposing credentials in environment variables, you can use a
YAML configuration file.

**Default locations** (checked in order):

1. `~/.config/sqlcheck/connections.yaml`
2. `~/.dtk/connections.yml`

You can override the location using:

```bash
export SQLCHECK_CONNECTIONS_FILE="/path/to/your/connections.yaml"
```

**Example `~/.config/sqlcheck/connections.yaml`:**

```yaml
dev:
  drivername: postgresql
  username: myuser
  password: ${DB_PASSWORD}  # Environment variables are expanded
  host: localhost
  port: 5432
  database: testdb

snowflake_prod:
  drivername: snowflake
  username: my_user
  password: ${SNOWFLAKE_PASSWORD}
  host: my_account
  database: ANALYTICS
  schema: PUBLIC
  query:
    warehouse: COMPUTE_WH
    role: ANALYST

# Simple URL format also works
local: "sqlite:///tmp/local.db"
```

**Usage:**

```bash
# Uses connection defined in YAML
sqlcheck run tests/ --connection dev

# Environment variables in YAML are expanded
export DB_PASSWORD="secret123"
sqlcheck run tests/ --connection dev
```

### Direct URL

You can also pass a connection URL directly (useful for testing):

```bash
sqlcheck run tests/ --connection "sqlite:///tmp/test.db"
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

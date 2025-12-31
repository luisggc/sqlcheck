from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlcheck.adapters.duckdb import DuckDBAdapter
from sqlcheck.functions import default_registry
from sqlcheck.models import TestCase, TestResult
from sqlcheck.plugins import load_plugins
from sqlcheck.reports import write_json, write_junit, write_plan
from sqlcheck.runner import build_test_case, discover_files, run_cases


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sqlcheck", description="Run SQL test files.")
    parser.add_argument("target", type=Path, help="Target file or directory to scan")
    parser.add_argument(
        "--pattern",
        default="**/*.sqltest",
        help="Glob pattern for test discovery (default: **/*.sqltest)",
    )
    parser.add_argument("--workers", type=int, default=5, help="Number of worker threads")
    parser.add_argument(
        "--engine",
        choices=["duckdb"],
        default="duckdb",
        help="Execution engine adapter",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        help="Write JSON report to path",
    )
    parser.add_argument(
        "--junit",
        dest="junit_path",
        type=Path,
        help="Write JUnit XML report to path",
    )
    parser.add_argument(
        "--plan-dir",
        dest="plan_dir",
        type=Path,
        help="Write per-test plan JSON files to this directory",
    )
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Plugin module path to load (can be repeated)",
    )
    parser.add_argument(
        "--duckdb-db",
        dest="duckdb_db",
        default=":memory:",
        help="DuckDB database path (default :memory:)",
    )
    return parser


def _render_result(result: TestResult) -> str:
    lines = [f"{result.case.metadata.name} [{result.case.path}]"]
    if result.success:
        lines.append("  PASS")
    else:
        lines.append("  FAIL")
        for func_result in result.function_results:
            if not func_result.success:
                message = func_result.message or "Expectation failed"
                lines.append(f"    - {func_result.name}: {message}")
        if result.output.stderr:
            lines.append("  STDERR:")
            lines.extend(f"    {line}" for line in result.output.stderr.splitlines())
        if result.output.stdout:
            lines.append("  STDOUT:")
            lines.extend(f"    {line}" for line in result.output.stdout.splitlines())
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    target = args.target
    paths = discover_files(target, args.pattern)
    if not paths:
        print("No test files found.")
        return 1

    cases: list[TestCase] = [build_test_case(path) for path in paths]

    registry = default_registry()
    if args.plugin:
        load_plugins(args.plugin, registry)

    if args.engine == "duckdb":
        adapter = DuckDBAdapter(database=args.duckdb_db)
    else:
        raise ValueError(f"Unsupported engine: {args.engine}")

    results = run_cases(cases, adapter, registry, workers=args.workers)

    for result in results:
        print(_render_result(result))

    if args.json_path:
        write_json(results, args.json_path)
    if args.junit_path:
        write_junit(results, args.junit_path)
    if args.plan_dir:
        args.plan_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            relative_name = str(result.case.path).replace("/", "__").replace("\\", "__")
            plan_path = args.plan_dir / f"{relative_name}.plan.json"
            write_plan(result, plan_path)

    failures = [result for result in results if not result.success]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

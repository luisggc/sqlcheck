import unittest
from pathlib import Path

from sqlcheck.db_connector import DBConnector, ExecutionResult
from sqlcheck.functions import FunctionRegistry, default_registry
from sqlcheck.models import ExecutionOutput, ExecutionStatus, FunctionResult, SQLParsed
from sqlcheck.runner import build_test_case, run_cases, run_test_case


class FakeAdapter(DBConnector):
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed

    def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
        status = ExecutionStatus(
            success=self.succeed,
            returncode=0 if self.succeed else 1,
            duration_s=0.01,
        )
        output = ExecutionOutput(
            stdout="ok" if self.succeed else "",
            stderr="" if self.succeed else "boom",
            rows=[[0]] if self.succeed else [],
        )
        return ExecutionResult(status=status, output=output)


class TestRunner(unittest.TestCase):
    def test_build_test_case_defaults_to_success(self) -> None:
        path = Path("/tmp/default.sql")
        path.write_text("SELECT 1;", encoding="utf-8")
        case = build_test_case(path)
        self.assertEqual(len(case.directives), 1)
        self.assertEqual(case.directives[0].name, "success")
        path.unlink()

    def test_run_test_case_success(self) -> None:
        path = Path("/tmp/success.sql")
        path.write_text("SELECT 1; {{ success() }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(True), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_run_test_case_failure_expectation(self) -> None:
        path = Path("/tmp/fail.sql")
        path.write_text("SELECT 1; {{ fail(error_match='boom') }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(False), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_run_cases_parallel_and_serial(self) -> None:
        path_a = Path("/tmp/parallel.sql")
        path_b = Path("/tmp/serial.sql")
        path_a.write_text("SELECT 1;", encoding="utf-8")
        path_b.write_text("SELECT 2; {{ success(serial=True) }}", encoding="utf-8")
        cases = [build_test_case(path_a), build_test_case(path_b)]
        results = run_cases(cases, FakeAdapter(True), default_registry(), workers=2)
        self.assertEqual(len(results), 2)
        path_a.unlink()
        path_b.unlink()

    def test_custom_registry_function(self) -> None:
        path = Path("/tmp/custom.sql")
        path.write_text("SELECT 1; {{ custom(check='ok') }}", encoding="utf-8")
        case = build_test_case(path)

        registry = FunctionRegistry()

        def custom(sql_parsed, status, output, check: str):
            self.assertEqual(check, "ok")
            return FunctionResult(name="custom", success=True, message=None)

        registry.register("custom", custom)
        result = run_test_case(case, FakeAdapter(True), registry)
        self.assertTrue(result.status.success)
        path.unlink()

    def test_expect_success_but_fails(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures_false_positives"
        path = fixtures_dir / "expect_success_but_fail.sql"
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(False), default_registry())
        self.assertFalse(result.success)
        self.assertEqual(result.function_results[0].message, "Expected success but execution failed")

    def test_expect_failure_but_succeeds(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures_false_positives"
        path = fixtures_dir / "expect_fail_but_succeed.sql"
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(True), default_registry())
        self.assertFalse(result.success)
        self.assertEqual(result.function_results[0].message, "Expected failure but execution succeeded")

    def test_assess_matches_stdout_and_stderr(self) -> None:
        path = Path("/tmp/assess-output.sql")
        path.write_text(
            "SELECT 1; {{ assess(stdout_match='ok', stderr_match='re:warn') }}",
            encoding="utf-8",
        )
        case = build_test_case(path)

        class OutputAdapter(DBConnector):
            def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                status = ExecutionStatus(success=True, returncode=0, duration_s=0.01)
                output = ExecutionOutput(stdout="ok", stderr="warning", rows=[])
                return ExecutionResult(status=status, output=output)

        result = run_test_case(case, OutputAdapter(), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_assess_matches_result_default_cell(self) -> None:
        path = Path("/tmp/assess-result.sql")
        path.write_text("SELECT 1; {{ assess(result_equals=0) }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(True), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_assess_matches_output_rows(self) -> None:
        path = Path("/tmp/assess-rows.sql")
        path.write_text("SELECT 1; {{ assess(output_match='1\\t2') }}", encoding="utf-8")
        case = build_test_case(path)

        class RowsAdapter(DBConnector):
            def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                status = ExecutionStatus(success=True, returncode=0, duration_s=0.01)
                output = ExecutionOutput(stdout="", stderr="", rows=[[1, 2]])
                return ExecutionResult(status=status, output=output)

        result = run_test_case(case, RowsAdapter(), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_assess_fixture_stdout_stderr(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_stdout_stderr.sql"
        case = build_test_case(path)

        class OutputAdapter(DBConnector):
            def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                status = ExecutionStatus(success=True, returncode=0, duration_s=0.01)
                output = ExecutionOutput(stdout="ok", stderr="warning", rows=[])
                return ExecutionResult(status=status, output=output)

        result = run_test_case(case, OutputAdapter(), default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_error_match(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_error_match.sql"
        case = build_test_case(path)

        class ErrorAdapter(DBConnector):
            def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                status = ExecutionStatus(success=False, returncode=1, duration_s=0.01)
                output = ExecutionOutput(stdout="", stderr="boom", rows=[])
                return ExecutionResult(status=status, output=output)

        result = run_test_case(case, ErrorAdapter(), default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_output_match(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_output_match.sql"
        case = build_test_case(path)

        class RowsAdapter(DBConnector):
            def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                status = ExecutionStatus(success=True, returncode=0, duration_s=0.01)
                output = ExecutionOutput(stdout="", stderr="", rows=[[1, 2]])
                return ExecutionResult(status=status, output=output)

        result = run_test_case(case, RowsAdapter(), default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_result_cells(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_result_cells.sql"
        case = build_test_case(path)

        class ResultAdapter(DBConnector):
            def execute(self, sql_parsed: SQLParsed, timeout: float | None = None) -> ExecutionResult:
                status = ExecutionStatus(success=True, returncode=0, duration_s=0.01)
                output = ExecutionOutput(stdout="", stderr="", rows=[[0, 2]])
                return ExecutionResult(status=status, output=output)

        result = run_test_case(case, ResultAdapter(), default_registry())
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

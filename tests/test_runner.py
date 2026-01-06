import unittest
from pathlib import Path

from sqlcheck.function_context import current_context
from sqlcheck.function_registry import FunctionRegistry, default_registry
from sqlcheck.models import ExecutionResult, FunctionResult
from sqlcheck.runner import build_test_case, run_cases, run_test_case


TEST_CONNECTION = "sqlite:///:memory:"


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
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_run_test_case_failure_expectation(self) -> None:
        path = Path("/tmp/fail.sql")
        path.write_text("SELECT * FROM nonexistent_table; {{ fail(match=\"'no such table' in error_message\") }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_run_cases_parallel_and_serial(self) -> None:
        path_a = Path("/tmp/parallel.sql")
        path_b = Path("/tmp/serial.sql")
        path_a.write_text("SELECT 1;", encoding="utf-8")
        path_b.write_text("SELECT 2; {{ success(serial=True) }}", encoding="utf-8")
        cases = [build_test_case(path_a), build_test_case(path_b)]
        results = run_cases(cases, TEST_CONNECTION, default_registry(), workers=2)
        self.assertEqual(len(results), 2)
        path_a.unlink()
        path_b.unlink()

    def test_custom_registry_function(self) -> None:
        path = Path("/tmp/custom.sql")
        path.write_text("SELECT 1; {{ custom(check='ok') }}", encoding="utf-8")
        case = build_test_case(path)

        registry = FunctionRegistry()

        def custom(check: str):
            context = current_context()
            self.assertEqual(context.status.success, True)
            self.assertEqual(check, "ok")
            return FunctionResult(name="custom", success=True, message=None)

        registry.register("custom", custom)
        result = run_test_case(case, TEST_CONNECTION, registry)
        self.assertTrue(result.status.success)
        path.unlink()

    def test_expect_success_but_fails(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures_false_positives"
        path = fixtures_dir / "expect_success_but_fail.sql"
        case = build_test_case(path)
        # Modify the SQL to ensure it fails
        path_temp = Path("/tmp/expect_success_but_fail.sql")
        path_temp.write_text("SELECT * FROM nonexistent_table; {{ success() }}", encoding="utf-8")
        case = build_test_case(path_temp)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertFalse(result.success)
        path_temp.unlink()

    def test_expect_failure_but_succeeds(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures_false_positives"
        path = fixtures_dir / "expect_fail_but_succeed.sql"
        case = build_test_case(path)
        # Modify the SQL to ensure it succeeds
        path_temp = Path("/tmp/expect_fail_but_succeed.sql")
        path_temp.write_text("SELECT 1; {{ fail() }}", encoding="utf-8")
        case = build_test_case(path_temp)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertFalse(result.success)
        path_temp.unlink()

    def test_assess_matches_result_default_cell(self) -> None:
        path = Path("/tmp/assess-result.sql")
        path.write_text("SELECT 0; {{ assess(match=\"rows[0][0] == 0\") }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_assess_matches_output_rows(self) -> None:
        path = Path("/tmp/assess-rows.sql")
        path.write_text("SELECT 1 as col1, 2 as col2; {{ assess(match=\"rows[0][0] == 1 && rows[0][1] == 2\") }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_assess_fixture_check_regex(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_check_regex.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_check_complex(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_check_complex.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_check_comparisons(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_check_comparisons.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    # Skipping test_assess_fixture_error_match - requires fake adapter with error

    def test_assess_fixture_output_match(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_output_match.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_result_cells(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_result_cells.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_result_cells_two(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_result_cells_two.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_stdout_contains_column(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_stdout_contains_column.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_stdout_contains_value(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_stdout_contains_value.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_stdout_multiple_columns(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_stdout_multiple_columns.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_stderr_contains_error(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_stderr_contains_error.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)

    def test_assess_fixture_stderr_regex_match(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "assess_stderr_regex_match.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from sqlcheck.adapters.base import Adapter, ExecutionResult
from sqlcheck.functions import FunctionRegistry, default_registry
from sqlcheck.models import ExecutionOutput, ExecutionStatus, FunctionResult
from sqlcheck.runner import build_test_case, run_cases, run_test_case


class FakeAdapter(Adapter):
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed

    def execute(self, sql: str, timeout: float | None = None) -> ExecutionResult:
        status = ExecutionStatus(
            success=self.succeed,
            returncode=0 if self.succeed else 1,
            duration_s=0.01,
        )
        output = ExecutionOutput(stdout="ok" if self.succeed else "", stderr="" if self.succeed else "boom")
        return ExecutionResult(status=status, output=output)


class TestRunner(unittest.TestCase):
    def test_build_test_case_defaults_to_success(self) -> None:
        path = Path("/tmp/default.sqltest")
        path.write_text("SELECT 1;", encoding="utf-8")
        case = build_test_case(path)
        self.assertEqual(len(case.directives), 1)
        self.assertEqual(case.directives[0].name, "success")
        path.unlink()

    def test_run_test_case_success(self) -> None:
        path = Path("/tmp/success.sqltest")
        path.write_text("SELECT 1; {{ success() }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(True), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_run_test_case_failure_expectation(self) -> None:
        path = Path("/tmp/fail.sqltest")
        path.write_text("SELECT 1; {{ fail(error_contains='boom') }}", encoding="utf-8")
        case = build_test_case(path)
        result = run_test_case(case, FakeAdapter(False), default_registry())
        self.assertTrue(result.success)
        path.unlink()

    def test_run_cases_parallel_and_serial(self) -> None:
        path_a = Path("/tmp/parallel.sqltest")
        path_b = Path("/tmp/serial.sqltest")
        path_a.write_text("SELECT 1;", encoding="utf-8")
        path_b.write_text("SELECT 2; {{ success(serial=True) }}", encoding="utf-8")
        cases = [build_test_case(path_a), build_test_case(path_b)]
        results = run_cases(cases, FakeAdapter(True), default_registry(), workers=2)
        self.assertEqual(len(results), 2)
        path_a.unlink()
        path_b.unlink()

    def test_custom_registry_function(self) -> None:
        path = Path("/tmp/custom.sqltest")
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


if __name__ == "__main__":
    unittest.main()

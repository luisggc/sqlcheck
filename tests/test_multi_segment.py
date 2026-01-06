import tempfile
import unittest
from pathlib import Path

from sqlcheck.function_registry import default_registry
from sqlcheck.runner import build_test_case, run_test_case


TEST_CONNECTION = "sqlite:///:memory:"


class TestMultiSegmentExecution(unittest.TestCase):
    def test_directive_first_executes_each_segment(self) -> None:
        path = Path("/tmp/multi-segment.sql")
        path.write_text(
            "{{ assess(match=\"rows[0][0] == 1\") }}\n"
            "SELECT 1;\n"
            "{{ assess(match=\"rows[0][0] == 2\") }}\n"
            "SELECT 2;\n",
            encoding="utf-8",
        )
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)
        self.assertEqual(len(result.function_results), 2)
        path.unlink()

    def test_fail_fast_defaults_to_true(self) -> None:
        path = Path("/tmp/fail-fast.sql")
        path.write_text(
            "{{ assess(match=\"rows[0][0] == 2\") }}\n"
            "SELECT 1;\n"
            "{{ assess(match=\"rows[0][0] == 2\") }}\n"
            "SELECT 2;\n",
            encoding="utf-8",
        )
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertFalse(result.success)
        # Only first segment should execute (fail fast)
        self.assertEqual(len(result.function_results), 1)
        path.unlink()

    def test_exit_on_failure_false_continues(self) -> None:
        path = Path("/tmp/exit-on-failure.sql")
        path.write_text(
            "{{ assess(match=\"rows[0][0] == 2\", exit_on_failure=False) }}\n"
            "SELECT 1;\n"
            "{{ assess(match=\"rows[0][0] == 2\") }}\n"
            "SELECT 2;\n",
            encoding="utf-8",
        )
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertFalse(result.success)
        # Both segments should execute despite first failure
        self.assertEqual(len(result.function_results), 2)
        path.unlink()

    def test_session_reuse_across_segments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_path = Path(temp_dir) / "session.sql"
            sql_path.write_text(
                "{{ success() }}\n"
                "CREATE TEMP TABLE temp_items (id INTEGER);\n"
                "{{ success() }}\n"
                "INSERT INTO temp_items VALUES (1);\n"
                "{{ assess(match=\"rows[0][0] == 1\") }}\n"
                "SELECT COUNT(*) FROM temp_items;\n",
                encoding="utf-8",
            )
            case = build_test_case(sql_path)
            result = run_test_case(case, TEST_CONNECTION, default_registry())
            self.assertTrue(result.success)
            self.assertEqual(len(result.function_results), 3)

    def test_fixture_multi_segment_success(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        path = fixtures_dir / "multi_segment_success.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertTrue(result.success)
        self.assertEqual(len(result.function_results), 2)

    def test_fixture_exit_on_failure_continues(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures_false_positives"
        path = fixtures_dir / "multi_segment_exit_on_failure.sql"
        case = build_test_case(path)
        result = run_test_case(case, TEST_CONNECTION, default_registry())
        self.assertFalse(result.success)
        self.assertEqual(len(result.function_results), 2)


if __name__ == "__main__":
    unittest.main()

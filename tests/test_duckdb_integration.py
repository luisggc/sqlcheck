import shutil
import unittest
from pathlib import Path

from sqlcheck.adapters.duckdb import DuckDBAdapter
from sqlcheck.cli import main
from sqlcheck.functions import default_registry
from sqlcheck.runner import build_test_case, discover_files, run_cases


class TestDuckDBIntegration(unittest.TestCase):
    @unittest.skipUnless(shutil.which("duckdb"), "duckdb CLI not found in PATH")
    def test_runs_fixture_with_duckdb_cli(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        paths = discover_files(fixtures_dir, "**/*.sql")
        cases = [build_test_case(path) for path in paths]
        results = run_cases(cases, DuckDBAdapter(), default_registry(), workers=1)
        self.assertTrue(all(result.success for result in results))

    @unittest.skipUnless(shutil.which("duckdb"), "duckdb CLI not found in PATH")
    def test_cli_discovers_fixtures_directory(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        exit_code = main([str(fixtures_dir)])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

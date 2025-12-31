import shutil
import unittest
from pathlib import Path

from sqlcheck.adapters.duckdb import DuckDBAdapter
from typer.testing import CliRunner

from sqlcheck.cli import app
from sqlcheck.functions import default_registry
from sqlcheck.runner import build_test_case, discover_files, run_cases


class TestDuckDBIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

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
        result = self.runner.invoke(app, ["run", str(fixtures_dir)])
        self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()

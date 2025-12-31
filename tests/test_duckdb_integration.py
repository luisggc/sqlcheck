import shutil
import unittest
from pathlib import Path

from sqlcheck.adapters.duckdb import DuckDBAdapter
from sqlcheck.functions import default_registry
from sqlcheck.runner import build_test_case, run_test_case


class TestDuckDBIntegration(unittest.TestCase):
    @unittest.skipUnless(shutil.which("duckdb"), "duckdb CLI not found in PATH")
    def test_runs_fixture_with_duckdb_cli(self) -> None:
        sql_path = Path(__file__).resolve().parent / "fixtures" / "basic.sqltest"
        case = build_test_case(sql_path)
        result = run_test_case(case, DuckDBAdapter(), default_registry())
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

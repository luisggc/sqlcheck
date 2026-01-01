import tempfile
import unittest
from pathlib import Path

from sqlcheck.db_connector import SQLAlchemyConnector
from sqlcheck.function_registry import default_registry
from sqlcheck.runner import build_test_case, run_test_case


class TestSQLAlchemyIntegration(unittest.TestCase):
    def test_runs_sql_with_sqlalchemy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_path = Path(temp_dir) / "basic.sql"
            sql_path.write_text(
                "{{ assess(lambda r: r.data['id'][0] == 1) }}\n"
                "CREATE TABLE test_table (id INTEGER);\n"
                "INSERT INTO test_table VALUES (1);\n"
                "SELECT * FROM test_table;\n",
                encoding="utf-8",
            )
            case = build_test_case(sql_path)
            adapter = SQLAlchemyConnector("sqlite:///:memory:")
            result = run_test_case(case, adapter, default_registry())
            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

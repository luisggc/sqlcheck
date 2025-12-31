import unittest

from sqlcheck.adapters.sqlalchemy import SQLAlchemyAdapter


class TestSQLAlchemyAdapter(unittest.TestCase):
    def test_missing_driver_reports_install_hint(self) -> None:
        with self.assertRaises(ValueError) as context:
            SQLAlchemyAdapter("snowflake://user:pass@account/db/schema")

        message = str(context.exception)
        self.assertIn("snowflake", message)
        self.assertIn("snowflake-sqlalchemy", message)


if __name__ == "__main__":
    unittest.main()

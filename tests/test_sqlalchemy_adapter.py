import unittest

from sqlcheck.db_connector import SQLAlchemyConnector


class TestSQLAlchemyAdapter(unittest.TestCase):
    def test_missing_driver_reports_install_hint(self) -> None:
        with self.assertRaises(ValueError) as context:
            SQLAlchemyConnector("snowflake://user:pass@account/db/schema")

        message = str(context.exception)
        self.assertIn("snowflake", message)
        self.assertIn("snowflake-sqlalchemy", message)
        self.assertIn("Can't load plugin", message)


if __name__ == "__main__":
    unittest.main()

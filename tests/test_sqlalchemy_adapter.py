import unittest

from sqlcheck.db_connector import SQLAlchemyConnector


class TestSQLAlchemyAdapter(unittest.TestCase):
    def test_missing_driver_reports_install_hint(self) -> None:
        # Use oracle which is very unlikely to be installed
        with self.assertRaises(ValueError) as context:
            SQLAlchemyConnector("oracle://user:pass@localhost/db")

        message = str(context.exception)
        self.assertIn("oracle", message)
        self.assertIn("Missing SQLAlchemy driver", message)


if __name__ == "__main__":
    unittest.main()

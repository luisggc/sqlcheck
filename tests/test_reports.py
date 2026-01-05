import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from sqlcheck.function_registry import default_registry
from sqlcheck.reports import write_json, write_junit, write_plan
from sqlcheck.runner import build_test_case, run_test_case


TEST_CONNECTION = "sqlite:///:memory:"


class TestReports(unittest.TestCase):
    def test_reports_write_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sql_path = Path(temp_dir) / "sample.sql"
            sql_path.write_text("SELECT 1; {{ success() }}", encoding="utf-8")
            case = build_test_case(sql_path)
            result = run_test_case(case, TEST_CONNECTION, default_registry())

            json_path = Path(temp_dir) / "report.json"
            junit_path = Path(temp_dir) / "report.xml"
            plan_path = Path(temp_dir) / "plan.json"

            write_json([result], json_path)
            write_junit([result], junit_path)
            write_plan(result, plan_path)

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["name"], "sample")

            tree = ElementTree.parse(junit_path)
            self.assertEqual(tree.getroot().tag, "testsuite")

            plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan_payload["directives"][0]["name"], "success")


if __name__ == "__main__":
    unittest.main()

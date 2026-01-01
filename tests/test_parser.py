import unittest
from pathlib import Path

from sqlcheck.parser import DirectiveParseError, parse_directives, parse_file, strip_directives


class TestParser(unittest.TestCase):
    def test_parse_directives_extracts_calls(self) -> None:
        source = """
        SELECT 1;
        {{ success(name='ok', tags=['smoke']) }}
        {{ fail(error_match='boom') }}
        """
        directives = parse_directives(source)
        self.assertEqual([d.name for d in directives], ["success", "fail"])
        self.assertEqual(directives[0].kwargs["name"], "ok")
        self.assertEqual(directives[0].kwargs["tags"], ["smoke"])
        self.assertEqual(directives[1].kwargs["error_match"], "boom")

    def test_strip_directives_removes_blocks(self) -> None:
        source = "SELECT 1; {{ success() }} SELECT 2;"
        stripped = strip_directives(source)
        self.assertNotIn("success", stripped)
        self.assertIn("SELECT 1", stripped)
        self.assertIn("SELECT 2", stripped)

    def test_parse_file_splits_statements(self) -> None:
        path = Path("/tmp/test.sql")
        path.write_text("SELECT 1; SELECT 2;", encoding="utf-8")
        parsed = parse_file(path)
        self.assertEqual(len(parsed.sql_parsed.statements), 2)
        self.assertEqual(parsed.sql_parsed.statements[0].text, "SELECT 1")
        self.assertEqual(parsed.sql_parsed.statements[1].text, "SELECT 2")
        path.unlink()

    def test_parse_directives_rejects_kw_splat(self) -> None:
        with self.assertRaises(DirectiveParseError):
            parse_directives("{{ success(**{'a': 1}) }}")


if __name__ == "__main__":
    unittest.main()

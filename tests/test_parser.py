import unittest
from pathlib import Path

from sqlcheck.parser import DirectiveParseError, parse_file


class TestParser(unittest.TestCase):
    def test_parse_directives_extracts_calls(self) -> None:
        """Test that directives are extracted correctly via Jinja parsing."""
        path = Path("/tmp/test.sql")
        source = """
        {{ success(name='ok', tags=['smoke']) }}
        SELECT 1;
        {{ fail(match="'boom' in error_message") }}
        SELECT 2;
        """
        path.write_text(source, encoding="utf-8")

        try:
            parsed = parse_file(path)
            directives = parsed.directives

            self.assertEqual([d.name for d in directives], ["success", "fail"])
            self.assertEqual(directives[0].kwargs["name"], "ok")
            self.assertEqual(directives[0].kwargs["tags"], ["smoke"])
            self.assertEqual(directives[1].kwargs["match"], "'boom' in error_message")
        finally:
            path.unlink()

    def test_strip_directives_removes_blocks(self) -> None:
        """Test that directive markers are removed from SQL."""
        path = Path("/tmp/test.sql")
        source = "{{ success() }} SELECT 1; {{ assess(match='true') }} SELECT 2;"
        path.write_text(source, encoding="utf-8")

        try:
            parsed = parse_file(path)
            stripped = parsed.sql_parsed.source

            self.assertNotIn("success", stripped)
            self.assertNotIn("assess", stripped)
            self.assertNotIn("{{", stripped)
            self.assertIn("SELECT 1", stripped)
            self.assertIn("SELECT 2", stripped)
        finally:
            path.unlink()

    def test_parse_file_splits_statements(self) -> None:
        """Test that SQL statements are split correctly."""
        path = Path("/tmp/test.sql")
        path.write_text("SELECT 1; SELECT 2;", encoding="utf-8")

        try:
            parsed = parse_file(path)
            self.assertEqual(len(parsed.sql_parsed.statements), 2)
            self.assertEqual(parsed.sql_parsed.statements[0].text, "SELECT 1")
            self.assertEqual(parsed.sql_parsed.statements[1].text, "SELECT 2")
        finally:
            path.unlink()

    def test_parse_directives_rejects_kw_splat(self) -> None:
        """Test that undefined variables in SQL (not directives) raise errors."""
        path = Path("/tmp/test.sql")
        # Undefined variable should raise error
        path.write_text("SELECT * FROM {{ undefined_table }};", encoding="utf-8")

        try:
            with self.assertRaises(DirectiveParseError):
                parse_file(path)
        finally:
            if path.exists():
                path.unlink()

    def test_trailing_directive_has_no_segment(self) -> None:
        path = Path("/tmp/test.sql")
        source = "SELECT 1; {{ success() }}"
        path.write_text(source, encoding="utf-8")

        try:
            parsed = parse_file(path)
            self.assertEqual(len(parsed.segments), 0)
        finally:
            if path.exists():
                path.unlink()

    def test_trailing_directive_after_multiple_statements_has_no_segment(self) -> None:
        path = Path("/tmp/test.sql")
        source = (
            "CREATE TABLE items (id INT); "
            "SELECT 1; "
            "{{ assess(match=\"statement_count == 2\") }}"
        )
        path.write_text(source, encoding="utf-8")

        try:
            parsed = parse_file(path)
            self.assertEqual(len(parsed.segments), 0)
        finally:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()

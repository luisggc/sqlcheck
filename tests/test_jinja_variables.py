"""Tests for Jinja template variable support."""

from pathlib import Path

from sqlcheck.discovery import build_test_case
from sqlcheck.execution import run_test_case
from sqlcheck.function_registry import default_registry
from sqlcheck.parser import DirectiveParseError

TEST_CONNECTION = "sqlite:///:memory:"


def test_basic_variable_substitution():
    """Test basic Jinja variable renders in SQL and directive."""
    path = Path(__file__).parent / "fixtures_jinja" / "jinja_env_variable.sql"
    template_vars = {"env": "prod"}
    case = build_test_case(path, template_vars=template_vars)

    # Verify variable was rendered in SQL
    assert "prod_test_data" in case.sql_parsed.source
    assert "{{ env }}" not in case.sql_parsed.source

    # Verify variable was rendered in directive name
    assert case.metadata.name == "test on prod environment"

    # Verify variables stored in metadata
    assert case.metadata.template_vars == {"env": "prod"}

    # Run the test to ensure it executes successfully
    result = run_test_case(case, TEST_CONNECTION, default_registry())
    assert result.success


def test_multiple_variables():
    """Test multiple variables in same file."""
    sql_content = """
    {{ assess(match="statement_count == 2") }}
    CREATE TABLE {{ env }}_{{ region }}_data (id INT);
    SELECT '{{ env }}' as environment, '{{ region }}' as region;
    """
    path = Path("/tmp/jinja_multi.sql")
    path.write_text(sql_content, encoding="utf-8")

    try:
        template_vars = {"env": "prod", "region": "us-east-1"}
        case = build_test_case(path, template_vars=template_vars)

        assert "prod_us-east-1_data" in case.sql_parsed.source
        assert case.metadata.template_vars == template_vars

        result = run_test_case(case, TEST_CONNECTION, default_registry())
        assert result.success
    finally:
        path.unlink()


def test_undefined_variable_error():
    """Test that undefined variables cause immediate error."""
    sql_content = "SELECT * FROM {{ undefined_var }}_table;"
    path = Path("/tmp/jinja_undefined.sql")
    path.write_text(sql_content, encoding="utf-8")

    try:
        # Should raise DirectiveParseError wrapping TemplateRenderError
        try:
            build_test_case(path, template_vars={})
            assert False, "Expected DirectiveParseError"
        except DirectiveParseError as exc:
            assert "undefined" in str(exc).lower()
            assert "undefined_var" in str(exc)
    finally:
        path.unlink()


def test_no_variables_passthrough():
    """Test that files work without any variables."""
    sql_content = "{{ success() }}\nSELECT 1;"
    path = Path("/tmp/jinja_none.sql")
    path.write_text(sql_content, encoding="utf-8")

    try:
        # Should work with None or empty dict
        case1 = build_test_case(path, template_vars=None)
        result1 = run_test_case(case1, TEST_CONNECTION, default_registry())
        assert result1.success

        case2 = build_test_case(path, template_vars={})
        result2 = run_test_case(case2, TEST_CONNECTION, default_registry())
        assert result2.success
    finally:
        path.unlink()


def test_directives_not_rendered_by_jinja():
    """Ensure directive function calls pass through Jinja unchanged."""
    sql_content = """
    {{ success(name='test') }}
    {{ assess(match='rows.size() == 1') }}
    SELECT 1;
    """
    path = Path("/tmp/jinja_directives.sql")
    path.write_text(sql_content, encoding="utf-8")

    try:
        case = build_test_case(path, template_vars={"env": "prod"})

        # Directives should be parsed correctly (not consumed by Jinja)
        assert len(case.directives) == 2
        assert case.directives[0].name == "success"
        assert case.directives[1].name == "assess"

        result = run_test_case(case, TEST_CONNECTION, default_registry())
        assert result.success
    finally:
        path.unlink()


def test_variable_in_assessment_expression():
    """Test using variables inside CEL assessment expressions."""
    sql_content = """
    {{ assess(match="stdout.contains('" ~ expected ~ "')") }}
    SELECT '{{ expected }}' as value;
    """
    path = Path("/tmp/jinja_assess.sql")
    path.write_text(sql_content, encoding="utf-8")

    try:
        template_vars = {"expected": "hello_world"}
        case = build_test_case(path, template_vars=template_vars)

        # Both the SQL and the CEL expression should contain the rendered value
        assert "hello_world" in case.sql_parsed.source

        result = run_test_case(case, TEST_CONNECTION, default_registry())
        assert result.success
    finally:
        path.unlink()

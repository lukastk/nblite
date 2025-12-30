"""
Tests for the directive system (Milestone 2).
"""

import pytest

from nblite.core.directive import (
    Directive,
    DirectiveDefinition,
    DirectiveError,
    clear_directive_definitions,
    get_directive_definition,
    get_source_without_directives,
    list_directive_definitions,
    parse_directives_from_source,
    register_directive,
    _register_builtin_directives,
)


class TestDirectiveDefinition:
    def test_create_basic_definition(self) -> None:
        """Test creating a basic directive definition."""
        defn = DirectiveDefinition(name="test_directive")
        assert defn.name == "test_directive"
        assert defn.in_topmatter is True
        assert defn.value_parser is None
        assert defn.allows_inline is False
        assert defn.description == ""

    def test_create_inline_definition(self) -> None:
        """Test creating a definition that allows inline."""
        defn = DirectiveDefinition(
            name="func_return_line",
            in_topmatter=False,
            allows_inline=True,
            description="Prepend return to this line",
        )
        assert defn.allows_inline is True
        assert defn.in_topmatter is False
        assert defn.description == "Prepend return to this line"

    def test_definition_with_parser(self) -> None:
        """Test definition with custom value parser."""
        defn = DirectiveDefinition(
            name="test_dir",
            value_parser=lambda v: v.upper(),
        )
        assert defn.value_parser is not None
        assert defn.value_parser("hello") == "HELLO"


class TestDirectiveRegistry:
    def setup_method(self) -> None:
        """Reset registry to built-in directives before each test."""
        clear_directive_definitions()
        _register_builtin_directives()

    def test_register_and_retrieve(self) -> None:
        """Test registering and retrieving directives."""
        defn = DirectiveDefinition(name="custom_test_directive")
        register_directive(defn)
        retrieved = get_directive_definition("custom_test_directive")
        assert retrieved is not None
        assert retrieved.name == "custom_test_directive"

    def test_builtin_directives_registered(self) -> None:
        """Test that built-in directives are registered."""
        assert get_directive_definition("export") is not None
        assert get_directive_definition("default_exp") is not None
        assert get_directive_definition("func_return_line") is not None
        assert get_directive_definition("hide") is not None
        assert get_directive_definition("eval") is not None

    def test_unknown_directive_returns_none(self) -> None:
        """Test unknown directive returns None."""
        result = get_directive_definition("nonexistent_directive_xyz")
        assert result is None

    def test_list_directive_definitions(self) -> None:
        """Test listing all registered directives."""
        definitions = list_directive_definitions()
        assert len(definitions) > 0
        names = [d.name for d in definitions]
        assert "export" in names
        assert "default_exp" in names


class TestDirectiveParsing:
    def test_parse_simple_directive(self) -> None:
        """Test parsing a simple directive."""
        source = "#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "export"
        assert directives[0].value == ""

    def test_parse_directive_with_value(self) -> None:
        """Test parsing directive with value."""
        source = "#|default_exp utils.helpers"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "default_exp"
        assert directives[0].value == "utils.helpers"
        assert directives[0].value_parsed == "utils.helpers"

    def test_parse_directive_with_colon(self) -> None:
        """Test parsing directive with colon syntax."""
        source = "#|eval: false"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "eval"
        assert directives[0].value == "false"
        # value_parsed should be False (using _parse_bool_false)
        assert directives[0].value_parsed is False

    def test_parse_multiline_directive(self) -> None:
        """Test parsing multi-line directive with continuation."""
        source = "#|directive_name \\\n#   value1 \\\n#   value2"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert "value1" in directives[0].value
        assert "value2" in directives[0].value

    def test_parse_inline_directive(self) -> None:
        """Test parsing inline directive after code."""
        source = "x = 42 #|func_return_line"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "func_return_line"
        assert directives[0].py_code == "x = 42 "

    def test_parse_escaped_backslash(self) -> None:
        """Test parsing directive with escaped backslash."""
        source = "#|directive_name path\\\\to\\\\file"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].value == "path\\to\\file"

    def test_parse_multiple_directives(self) -> None:
        """Test parsing multiple directives in one cell."""
        source = "#|default_exp utils\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert len(directives) == 2
        assert directives[0].name == "default_exp"
        assert directives[1].name == "export"

    def test_directive_line_numbers(self) -> None:
        """Test that directive line numbers are correct."""
        source = "#|default_exp utils\n\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert directives[0].line_num == 0
        assert directives[1].line_num == 2

    def test_parse_export_to_with_order(self) -> None:
        """Test parsing export_to directive with order value."""
        source = "#|export_to utils.helpers 50"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "export_to"
        assert directives[0].value_parsed["module"] == "utils.helpers"
        assert directives[0].value_parsed["order"] == 50

    def test_parse_export_to_default_order(self) -> None:
        """Test parsing export_to directive with default order."""
        source = "#|export_to utils.helpers"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].value_parsed["module"] == "utils.helpers"
        assert directives[0].value_parsed["order"] == 100

    def test_parse_export_as_func(self) -> None:
        """Test parsing export_as_func directive."""
        source = "#|export_as_func true"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].value_parsed is True

        source2 = "#|export_as_func false"
        directives2 = parse_directives_from_source(source2)
        assert directives2[0].value_parsed is False


class TestTopmatter:
    def test_topmatter_valid(self) -> None:
        """Test valid topmatter directive."""
        source = "#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert directives[0].is_in_topmatter() is True

    def test_topmatter_with_whitespace(self) -> None:
        """Test topmatter with leading whitespace/empty lines."""
        source = "\n\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert directives[0].is_in_topmatter() is True

    def test_topmatter_after_comment(self) -> None:
        """Test directive after comment is still topmatter."""
        source = "# This is a comment\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert directives[0].is_in_topmatter() is True

    def test_not_topmatter_after_code(self) -> None:
        """Test directive after code is not topmatter."""
        source = "x = 1\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert directives[0].is_in_topmatter() is False

    def test_inline_directive_not_in_topmatter(self) -> None:
        """Test inline directive is not in topmatter."""
        source = "x = 42 #|func_return_line"
        directives = parse_directives_from_source(source)
        assert directives[0].is_in_topmatter() is False

    def test_topmatter_validation_passes(self) -> None:
        """Test topmatter validation passes for valid directive."""
        source = "#|export\ndef foo(): pass"
        # Should not raise
        directives = parse_directives_from_source(source, validate=True)
        assert len(directives) == 1

    def test_topmatter_validation_fails_after_code(self) -> None:
        """Test topmatter validation fails for directive after code."""
        source = "x = 1\n#|export\ndef foo(): pass"
        with pytest.raises(DirectiveError, match="must be in topmatter"):
            parse_directives_from_source(source, validate=True)

    def test_inline_allowed_for_func_return_line(self) -> None:
        """Test inline is allowed for func_return_line directive."""
        source = "def foo():\n    result #|func_return_line"
        # Should not raise - func_return_line allows inline
        directives = parse_directives_from_source(source, validate=True)
        assert len(directives) == 1


class TestSourceWithoutDirectives:
    def test_remove_simple_directive(self) -> None:
        """Test removing a simple directive line."""
        source = "#|export\ndef foo(): pass"
        result = get_source_without_directives(source)
        assert "#|export" not in result
        assert "def foo(): pass" in result

    def test_remove_multiple_directives(self) -> None:
        """Test removing multiple directive lines."""
        source = "#|default_exp utils\n#|export\ndef foo(): pass"
        result = get_source_without_directives(source)
        assert "#|default_exp" not in result
        assert "#|export" not in result
        assert "def foo(): pass" in result

    def test_keep_inline_code(self) -> None:
        """Test keeping code before inline directive."""
        source = "x = 42 #|func_return_line"
        result = get_source_without_directives(source)
        assert "x = 42" in result
        assert "#|func_return_line" not in result

    def test_remove_multiline_directive(self) -> None:
        """Test removing multi-line directive."""
        source = "#|directive \\\n#   continuation\ndef foo(): pass"
        result = get_source_without_directives(source)
        assert "#|directive" not in result
        assert "continuation" not in result
        assert "def foo(): pass" in result

    def test_preserve_regular_comments(self) -> None:
        """Test that regular comments are preserved."""
        source = "# Regular comment\n#|export\ndef foo(): pass"
        result = get_source_without_directives(source)
        assert "# Regular comment" in result
        assert "#|export" not in result


class TestDirectiveValueParsing:
    def setup_method(self) -> None:
        """Reset registry to built-in directives before each test."""
        clear_directive_definitions()
        _register_builtin_directives()

    def test_custom_value_parser(self) -> None:
        """Test custom value parser is called."""
        register_directive(
            DirectiveDefinition(
                name="custom_parsed",
                value_parser=lambda v: {"key": v.strip(), "length": len(v.strip())},
            )
        )
        source = "#|custom_parsed hello world"
        directives = parse_directives_from_source(source)
        assert directives[0].value_parsed["key"] == "hello world"
        assert directives[0].value_parsed["length"] == 11

    def test_parser_error_raises_directive_error(self) -> None:
        """Test that parser errors raise DirectiveError."""
        def bad_parser(value: str) -> int:
            return int(value)  # Will fail for non-numeric

        register_directive(
            DirectiveDefinition(
                name="bad_parsed",
                value_parser=bad_parser,
            )
        )
        source = "#|bad_parsed not_a_number"
        with pytest.raises(DirectiveError, match="Failed to parse"):
            parse_directives_from_source(source)

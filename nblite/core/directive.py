"""
Directive parsing and representation for nblite.

Directives are special comments in notebook cells that control behavior:
    #|export          - Export cell to module
    #|default_exp mod - Set default export module
    #|hide            - Hide from documentation
"""

from __future__ import annotations

import io
import re
import tokenize
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from nblite.extensions import HookRegistry, HookType

if TYPE_CHECKING:
    from nblite.core.cell import Cell

__all__ = [
    "Directive",
    "DirectiveDefinition",
    "DirectiveError",
    "register_directive",
    "get_directive_definition",
    "list_directive_definitions",
    "parse_directives_from_source",
    "get_unrecognized_directives",
]


class DirectiveError(Exception):
    """Error raised when directive parsing or validation fails."""

    pass


@dataclass
class DirectiveDefinition:
    """
    Defines the rules for a directive.

    Attributes:
        name: Directive name (e.g., "export", "default_exp")
        in_topmatter: If True, directive must be placed in topmatter
                      (top of cell, before any code)
        value_parser: Optional function to parse the value string
        allows_inline: If True, directive can appear after code on same line
        description: Human-readable description
    """

    name: str
    in_topmatter: bool = True
    value_parser: Callable[[str], Any] | None = None
    allows_inline: bool = False
    description: str = ""


# Global registry for directive definitions
_directive_definitions: dict[str, DirectiveDefinition] = {}


def register_directive(definition: DirectiveDefinition) -> None:
    """Register a directive definition."""
    _directive_definitions[definition.name] = definition


def get_directive_definition(name: str) -> DirectiveDefinition | None:
    """Get the definition for a directive, or None if not registered."""
    return _directive_definitions.get(name)


def list_directive_definitions() -> list[DirectiveDefinition]:
    """List all registered directive definitions."""
    return list(_directive_definitions.values())


def get_unrecognized_directives(directives: list[Directive]) -> list[Directive]:
    """
    Get all unrecognized directives from a list of directives.

    Args:
        directives: List of Directive objects to check

    Returns:
        List of directives that are not registered in the directive definitions
    """
    return [d for d in directives if get_directive_definition(d.name) is None]


def clear_directive_definitions() -> None:
    """Clear all directive definitions. Useful for testing."""
    _directive_definitions.clear()


@dataclass
class Directive:
    """
    Represents a single directive in a notebook cell.

    Attributes:
        name: Directive name (e.g., "export", "default_exp")
        value: Raw string value after the directive name
        value_parsed: Parsed value (using registered parser, or same as value)
        line_num: Line number within the cell source (0-indexed)
        py_code: Code before the directive comment on this line (for inline)
        cell: Reference to the containing cell (optional, set later)
        _is_topmatter: Whether this directive is in the topmatter position
    """

    name: str
    value: str = ""
    value_parsed: Any = field(default=None, repr=False)
    line_num: int = 0
    py_code: str = ""
    cell: Cell | None = field(default=None, repr=False)
    _is_topmatter: bool = field(default=True, repr=False)

    def __post_init__(self) -> None:
        """Parse the value if a parser is registered."""
        if self.value_parsed is None:
            definition = get_directive_definition(self.name)
            if definition and definition.value_parser:
                try:
                    self.value_parsed = definition.value_parser(self.value)
                except Exception as e:
                    raise DirectiveError(
                        f"Failed to parse value for directive '{self.name}': {e}"
                    ) from e
            else:
                self.value_parsed = self.value

    def is_in_topmatter(self) -> bool:
        """Check if this directive is in the topmatter position."""
        return self._is_topmatter


# Regex pattern for parsing directives
# Matches: optional_code #|directive_name optional_value
# Handles continuation with backslash
DIRECTIVE_PATTERN = re.compile(
    r"^(?P<py_code>.*?)#\|(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::?\s*(?P<value>.*))?$"
)


def _is_code_line(line: str) -> bool:
    """Check if a line contains actual code (not just comments/whitespace/directives)."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return False
    return True


def _has_code_before(lines: list[str], line_num: int) -> bool:
    """Check if there's any code before the given line number."""
    for i in range(line_num):
        if _is_code_line(lines[i]):
            return True
    return False


def _get_string_ranges(source: str) -> list[tuple[int, int, int, int]]:
    """
    Get the ranges of all string literals in the source code.

    Uses Python's tokenize module to accurately identify strings,
    including multi-line strings, f-strings, raw strings, etc.

    Args:
        source: Python source code

    Returns:
        List of (start_row, start_col, end_row, end_col) tuples.
        Rows are 1-indexed (as returned by tokenize).
    """
    ranges: list[tuple[int, int, int, int]] = []

    # Token types to consider as string content
    # In Python 3.12+, f-strings are tokenized differently (PEP 701):
    # - FSTRING_START, FSTRING_MIDDLE, FSTRING_END instead of single STRING token
    string_token_types = {tokenize.STRING}

    # Add f-string token types if available (Python 3.12+)
    if hasattr(tokenize, "FSTRING_START"):
        string_token_types.add(tokenize.FSTRING_START)
        string_token_types.add(tokenize.FSTRING_MIDDLE)
        string_token_types.add(tokenize.FSTRING_END)

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type in string_token_types:
                # tok.start and tok.end are (row, col) tuples, 1-indexed rows
                ranges.append((tok.start[0], tok.start[1], tok.end[0], tok.end[1]))
    except tokenize.TokenizeError:
        # Handle incomplete/invalid Python code gracefully
        # Return empty list - directives will be parsed normally
        pass
    return ranges


def _is_position_in_string(
    line_num_0indexed: int,
    col: int,
    string_ranges: list[tuple[int, int, int, int]],
) -> bool:
    """
    Check if a position (line, col) falls inside any string range.

    Args:
        line_num_0indexed: 0-indexed line number
        col: Column position (0-indexed)
        string_ranges: List of (start_row, start_col, end_row, end_col),
                       where rows are 1-indexed

    Returns:
        True if the position is inside a string literal
    """
    # Convert to 1-indexed for comparison with tokenize output
    line_num = line_num_0indexed + 1

    for start_row, start_col, end_row, end_col in string_ranges:
        # Check if position is within this string range
        if start_row == end_row:
            # Single-line string
            if line_num == start_row and start_col <= col < end_col:
                return True
        else:
            # Multi-line string
            if line_num == start_row and col >= start_col:
                return True
            elif line_num == end_row and col < end_col:
                return True
            elif start_row < line_num < end_row:
                return True
    return False


def parse_directives_from_source(
    source: str,
    validate: bool = False,
    cell: Cell | None = None,
) -> list[Directive]:
    """
    Parse all directives from cell source code.

    Args:
        source: The cell source code
        validate: If True, validate topmatter requirements
        cell: Optional cell reference to attach to directives

    Returns:
        List of Directive objects found in the source

    Raises:
        DirectiveError: If validation fails (e.g., topmatter directive after code)

    Hooks triggered:
        DIRECTIVE_PARSED: For each directive (directive=directive, cell=cell)
    """
    directives: list[Directive] = []
    lines = source.split("\n")

    # Get string ranges to avoid parsing directives inside strings
    string_ranges = _get_string_ranges(source)

    i = 0
    while i < len(lines):
        line = lines[i]
        directive_start_line = i  # Track where directive starts
        match = DIRECTIVE_PATTERN.match(line)

        if match:
            py_code = match.group("py_code") or ""

            # Check if the #| is inside a string literal
            # The #| starts at the end of py_code
            directive_col = len(py_code)
            if _is_position_in_string(directive_start_line, directive_col, string_ranges):
                # Skip this match - it's inside a string
                i += 1
                continue

            name = match.group("name")
            value = match.group("value") or ""

            # Handle multi-line continuation
            while value.rstrip().endswith("\\") and i + 1 < len(lines):
                # Remove trailing backslash and continue
                value = value.rstrip()[:-1]
                i += 1
                next_line = lines[i]
                # Strip leading # and whitespace from continuation line
                continuation = next_line.lstrip()
                if continuation.startswith("#"):
                    continuation = continuation[1:].lstrip()
                value += continuation

            # Handle escaped backslashes (double backslash -> single)
            value = value.replace("\\\\", "\x00")  # Temporary placeholder
            value = value.replace("\\", "")  # Remove single backslashes (continuations)
            value = value.replace("\x00", "\\")  # Restore escaped backslashes
            value = value.strip()

            # Determine if directive is in topmatter
            # Topmatter = at top of cell before any code
            # A directive with py_code (inline) is NOT in topmatter
            has_inline_code = bool(py_code.strip())
            has_code_above = _has_code_before(lines, directive_start_line)

            is_topmatter = not has_inline_code and not has_code_above

            directive = Directive(
                name=name,
                value=value,
                line_num=directive_start_line,
                py_code=py_code,
                cell=cell,
                _is_topmatter=is_topmatter,
            )
            directives.append(directive)

            # Trigger DIRECTIVE_PARSED hook
            HookRegistry.trigger(
                HookType.DIRECTIVE_PARSED,
                directive=directive,
                cell=cell,
            )

            # Validate if requested
            if validate:
                definition = get_directive_definition(name)
                if definition:
                    if definition.in_topmatter and not directive.is_in_topmatter():
                        if has_inline_code and not definition.allows_inline:
                            raise DirectiveError(
                                f"Directive '{name}' must be in topmatter (found inline code: '{py_code.strip()}')"
                            )
                        elif has_code_above:
                            raise DirectiveError(
                                f"Directive '{name}' must be in topmatter (found after code)"
                            )

        i += 1

    return directives


def get_source_without_directives(source: str) -> str:
    """
    Remove all directive lines from source code.

    Args:
        source: The cell source code

    Returns:
        Source with directive lines removed
    """
    lines = source.split("\n")
    result_lines: list[str] = []

    # Get string ranges to avoid treating directives inside strings as real directives
    string_ranges = _get_string_ranges(source)

    i = 0
    while i < len(lines):
        line = lines[i]
        match = DIRECTIVE_PATTERN.match(line)

        if match:
            py_code = match.group("py_code") or ""

            # Check if the #| is inside a string literal
            directive_col = len(py_code)
            if _is_position_in_string(i, directive_col, string_ranges):
                # Not a real directive - keep the line as-is
                result_lines.append(line)
                i += 1
                continue

            value = match.group("value") or ""

            # Skip continuation lines
            while value.rstrip().endswith("\\") and i + 1 < len(lines):
                value = value.rstrip()[:-1]
                i += 1
                next_line = lines[i]
                continuation = next_line.lstrip()
                if continuation.startswith("#"):
                    continuation = continuation[1:].lstrip()
                value += continuation

            # If there's code before the directive, keep just the code
            if py_code.strip():
                result_lines.append(py_code.rstrip())
        else:
            result_lines.append(line)

        i += 1

    return "\n".join(result_lines)


# ============================================================================
# Built-in Directive Definitions
# ============================================================================


def _parse_bool_true(value: str) -> bool:
    """Parse value as boolean, True if 'true' (case-insensitive)."""
    return value.strip().lower() == "true"


def _parse_bool_false(value: str) -> bool:
    """Parse value as boolean, False if 'false' (case-insensitive)."""
    return value.strip().lower() != "false"


def _parse_export_order(value: str, default: int = 0) -> dict[str, int]:
    """Parse export order: '[ORDER]' -> {"order": int}."""
    value = value.strip()
    if not value:
        return {"order": default}
    try:
        return {"order": int(value)}
    except ValueError:
        return {"order": default}


def _parse_export(value: str) -> dict[str, int]:
    """Parse export directive: '#|export [ORDER]' -> {"order": int}. Default order: 0."""
    return _parse_export_order(value, default=0)


def _parse_exporti(value: str) -> dict[str, int]:
    """Parse exporti directive: '#|exporti [ORDER]' -> {"order": int}. Default order: 0."""
    return _parse_export_order(value, default=0)


def _parse_top_export(value: str) -> dict[str, int]:
    """Parse top_export directive: '#|top_export [ORDER]' -> {"order": int}. Default order: -1000."""
    return _parse_export_order(value, default=-1000)


def _parse_bottom_export(value: str) -> dict[str, int]:
    """Parse bottom_export directive: '#|bottom_export [ORDER]' -> {"order": int}. Default order: 1000."""
    return _parse_export_order(value, default=1000)


def _parse_export_to(value: str) -> dict[str, Any]:
    """Parse export_to value: 'module.path [ORDER]'."""
    parts = value.strip().split()
    if not parts:
        return {"module": "", "order": 1}

    module = parts[0]
    order = 1  # Default order

    if len(parts) > 1:
        try:
            order = int(parts[1])
        except ValueError:
            pass

    return {"module": module, "order": order}


def _register_builtin_directives() -> None:
    """Register all built-in directive definitions."""
    # Export directives
    register_directive(
        DirectiveDefinition(
            name="default_exp",
            in_topmatter=True,
            value_parser=str.strip,
            description="Set default export module path",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="export",
            in_topmatter=True,
            value_parser=_parse_export,
            description="Export cell to default module with optional order",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="exporti",
            in_topmatter=True,
            value_parser=_parse_exporti,
            description="Export cell as internal (not in __all__) with optional order",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="export_to",
            in_topmatter=True,
            value_parser=_parse_export_to,
            description="Export cell to specific module with optional order",
        )
    )

    # Function export directives
    register_directive(
        DirectiveDefinition(
            name="export_as_func",
            in_topmatter=True,
            value_parser=_parse_bool_true,
            description="Export notebook as callable function",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="set_func_signature",
            in_topmatter=True,
            description="Set function signature for export_as_func",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="top_export",
            in_topmatter=True,
            value_parser=_parse_top_export,
            description="Code placed at module level before function (function notebooks only)",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="bottom_export",
            in_topmatter=True,
            value_parser=_parse_bottom_export,
            description="Code placed at module level after function (function notebooks only)",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="func_return",
            in_topmatter=True,
            description="Prepend 'return' to first line of cell",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="func_return_line",
            in_topmatter=False,
            allows_inline=True,
            description="Prepend 'return' to this line (inline directive)",
        )
    )

    # Documentation directives
    register_directive(
        DirectiveDefinition(
            name="hide",
            in_topmatter=True,
            description="Hide cell from documentation",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="hide_input",
            in_topmatter=True,
            description="Hide input, show output in documentation",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="hide_output",
            in_topmatter=True,
            description="Show input, hide output in documentation",
        )
    )

    # Evaluation directives
    register_directive(
        DirectiveDefinition(
            name="eval",
            in_topmatter=True,
            value_parser=_parse_bool_false,
            description="Skip cell execution if 'false'",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="skip_evals",
            in_topmatter=True,
            description="Skip this and following cells during execution",
        )
    )
    register_directive(
        DirectiveDefinition(
            name="skip_evals_stop",
            in_topmatter=True,
            description="Resume cell execution",
        )
    )


# Register built-in directives on module load
_register_builtin_directives()

"""
Tests for the Cell class (Milestone 3).
"""

from nblite.core.cell import Cell, CellType


class TestCellCreation:
    def test_create_code_cell(self) -> None:
        """Test creating a code cell."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|export\ndef foo(): pass",
            index=0,
        )
        assert cell.cell_type == CellType.CODE
        assert cell.is_code is True
        assert cell.is_markdown is False
        assert cell.index == 0

    def test_create_markdown_cell(self) -> None:
        """Test creating a markdown cell."""
        cell = Cell(
            cell_type=CellType.MARKDOWN,
            source="# Hello World",
            index=1,
        )
        assert cell.cell_type == CellType.MARKDOWN
        assert cell.is_markdown is True
        assert cell.is_code is False

    def test_create_raw_cell(self) -> None:
        """Test creating a raw cell."""
        cell = Cell(
            cell_type=CellType.RAW,
            source="raw content",
            index=2,
        )
        assert cell.cell_type == CellType.RAW
        assert cell.is_raw is True

    def test_from_dict(self) -> None:
        """Test creating cell from dictionary."""
        data = {
            "cell_type": "code",
            "source": "#|export\ndef foo(): pass",
            "metadata": {"key": "value"},
            "outputs": [],
            "execution_count": 1,
        }
        cell = Cell.from_dict(data, index=0)
        assert cell.cell_type == CellType.CODE
        assert "#|export" in cell.source
        assert cell.metadata == {"key": "value"}
        assert cell.execution_count == 1

    def test_from_dict_source_as_list(self) -> None:
        """Test handling source as list of strings."""
        data = {
            "cell_type": "code",
            "source": ["#|export\n", "def foo():\n", "    pass"],
            "metadata": {},
            "outputs": [],
        }
        cell = Cell.from_dict(data, index=0)
        assert "#|export" in cell.source
        assert "def foo():" in cell.source

    def test_to_dict(self) -> None:
        """Test converting cell to dictionary."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="x = 1",
            metadata={"key": "value"},
            outputs=[{"output_type": "stream", "name": "stdout", "text": "1"}],
            execution_count=1,
        )
        data = cell.to_dict()
        assert data["cell_type"] == "code"
        assert data["source"] == "x = 1"
        assert data["metadata"] == {"key": "value"}
        assert data["outputs"] == [{"output_type": "stream", "name": "stdout", "text": "1"}]
        assert data["execution_count"] == 1

    def test_to_dict_markdown(self) -> None:
        """Test converting markdown cell to dictionary (no outputs)."""
        cell = Cell(
            cell_type=CellType.MARKDOWN,
            source="# Title",
            metadata={},
        )
        data = cell.to_dict()
        assert "outputs" not in data
        assert "execution_count" not in data


class TestCellDirectives:
    def test_cell_directives_property(self) -> None:
        """Test directives property parses directives."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|export\n#|hide\ndef foo(): pass",
        )
        directives = cell.directives
        assert "export" in directives
        assert "hide" in directives

    def test_has_directive(self) -> None:
        """Test has_directive method."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|export\ndef foo(): pass",
        )
        assert cell.has_directive("export") is True
        assert cell.has_directive("hide") is False

    def test_get_directive(self) -> None:
        """Test get_directive method."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|default_exp utils.helpers\ndef foo(): pass",
        )
        directive = cell.get_directive("default_exp")
        assert directive is not None
        assert directive.name == "default_exp"
        assert directive.value_parsed == "utils.helpers"

    def test_get_directive_not_found(self) -> None:
        """Test get_directive returns None when not found."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="def foo(): pass",
        )
        assert cell.get_directive("export") is None

    def test_get_directives(self) -> None:
        """Test get_directives returns list."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|export\n#|export\ndef foo(): pass",
        )
        directives = cell.get_directives("export")
        assert len(directives) == 2

    def test_markdown_cell_no_directives(self) -> None:
        """Test markdown cells have no directives."""
        cell = Cell(
            cell_type=CellType.MARKDOWN,
            source="#|export\nNot actually a directive",
        )
        assert len(cell.directives) == 0


class TestCellSourceWithoutDirectives:
    def test_source_without_directives(self) -> None:
        """Test source_without_directives removes directive lines."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|export\ndef foo(): pass",
        )
        result = cell.source_without_directives
        assert "#|export" not in result
        assert "def foo(): pass" in result

    def test_source_without_multiple_directives(self) -> None:
        """Test removing multiple directive lines."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="#|default_exp utils\n#|export\ndef foo(): pass",
        )
        result = cell.source_without_directives
        assert "#|default_exp" not in result
        assert "#|export" not in result
        assert "def foo(): pass" in result

    def test_source_without_directives_preserves_inline_code(self) -> None:
        """Test inline directive preserves code before it."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="x = 42 #|func_return_line",
        )
        result = cell.source_without_directives
        assert "x = 42" in result
        assert "#|func_return_line" not in result

    def test_source_without_directives_markdown(self) -> None:
        """Test markdown cell source unchanged."""
        cell = Cell(
            cell_type=CellType.MARKDOWN,
            source="# Title\nSome text",
        )
        assert cell.source_without_directives == cell.source


class TestCellRepr:
    def test_repr_short_source(self) -> None:
        """Test repr with short source."""
        cell = Cell(cell_type=CellType.CODE, source="x = 1", index=0)
        repr_str = repr(cell)
        assert "code" in repr_str
        assert "index=0" in repr_str
        assert "x = 1" in repr_str

    def test_repr_long_source(self) -> None:
        """Test repr truncates long source."""
        cell = Cell(
            cell_type=CellType.CODE,
            source="x = " + "1" * 100,
            index=5,
        )
        repr_str = repr(cell)
        assert "..." in repr_str
        assert "index=5" in repr_str

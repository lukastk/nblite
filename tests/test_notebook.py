"""
Tests for the Notebook class (Milestone 3).
"""

import json
from pathlib import Path

import pytest

from nblite.core.cell import Cell
from nblite.core.notebook import Format, Notebook


class TestNotebookCreation:
    def test_from_dict(self) -> None:
        """Test creating notebook from dictionary."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|default_exp utils",
                    "metadata": {},
                    "outputs": [],
                },
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                },
            ],
            "metadata": {"key": "value"},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        nb = Notebook.from_dict(data)
        assert len(nb.cells) == 2
        assert nb.metadata == {"key": "value"}
        assert nb.nbformat == 4

    def test_from_string_ipynb(self) -> None:
        """Test creating notebook from ipynb string."""
        content = json.dumps(
            {
                "cells": [
                    {"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb = Notebook.from_string(content, Format.IPYNB)
        assert len(nb.cells) == 1
        assert nb.cells[0].source == "x = 1"

    def test_from_string_percent(self) -> None:
        """Test creating notebook from percent format string."""
        content = """# %%
#|export
def foo():
    pass

# %% [markdown]
# Title
"""
        nb = Notebook.from_string(content, Format.PERCENT)
        assert len(nb.cells) == 2
        assert nb.cells[0].is_code
        assert nb.cells[1].is_markdown

    def test_from_file_ipynb(self, tmp_path: Path) -> None:
        """Test loading notebook from ipynb file."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef foo(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)

        nb = Notebook.from_file(nb_path)
        assert len(nb.cells) == 1
        assert nb.source_path == nb_path

    def test_from_file_percent(self, tmp_path: Path) -> None:
        """Test loading notebook from percent file."""
        pct_content = """# %%
#|export
def foo():
    pass
"""
        pct_path = tmp_path / "test.pct.py"
        pct_path.write_text(pct_content)

        nb = Notebook.from_file(pct_path)
        assert len(nb.cells) >= 1
        assert nb.source_path == pct_path


class TestNotebookDirectives:
    @pytest.fixture
    def sample_notebook(self) -> Notebook:
        """Create a sample notebook with directives."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|default_exp utils",
                    "metadata": {},
                    "outputs": [],
                },
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                },
                {"cell_type": "markdown", "source": "# Documentation", "metadata": {}},
                {
                    "cell_type": "code",
                    "source": "#|export\ndef bar(): pass",
                    "metadata": {},
                    "outputs": [],
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        return Notebook.from_dict(data)

    def test_directives_aggregated(self, sample_notebook: Notebook) -> None:
        """Test directives are aggregated from all cells."""
        directives = sample_notebook.directives
        assert "default_exp" in directives
        assert "export" in directives
        assert len(directives["export"]) == 2

    def test_get_directive(self, sample_notebook: Notebook) -> None:
        """Test get_directive returns first directive."""
        directive = sample_notebook.get_directive("default_exp")
        assert directive is not None
        assert directive.value_parsed == "utils"

    def test_get_directives(self, sample_notebook: Notebook) -> None:
        """Test get_directives returns all directives."""
        directives = sample_notebook.get_directives("export")
        assert len(directives) == 2

    def test_default_exp(self, sample_notebook: Notebook) -> None:
        """Test default_exp property."""
        assert sample_notebook.default_exp == "utils"

    def test_default_exp_none(self) -> None:
        """Test default_exp is None when not set."""
        data = {
            "cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        nb = Notebook.from_dict(data)
        assert nb.default_exp is None

    def test_exported_cells(self, sample_notebook: Notebook) -> None:
        """Test exported_cells property."""
        exported = sample_notebook.exported_cells
        assert len(exported) == 2
        assert all(cell.has_directive("export") for cell in exported)


class TestNotebookCellAccess:
    @pytest.fixture
    def sample_notebook(self) -> Notebook:
        """Create a sample notebook."""
        data = {
            "cells": [
                {"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []},
                {"cell_type": "markdown", "source": "# Title", "metadata": {}},
                {"cell_type": "code", "source": "y = 2", "metadata": {}, "outputs": []},
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        return Notebook.from_dict(data)

    def test_len(self, sample_notebook: Notebook) -> None:
        """Test len() returns cell count."""
        assert len(sample_notebook) == 3

    def test_iteration(self, sample_notebook: Notebook) -> None:
        """Test iteration over cells."""
        cells = list(sample_notebook)
        assert len(cells) == 3
        assert all(isinstance(c, Cell) for c in cells)

    def test_indexing(self, sample_notebook: Notebook) -> None:
        """Test cell indexing."""
        assert sample_notebook[0].source == "x = 1"
        assert sample_notebook[1].is_markdown
        assert sample_notebook[2].source == "y = 2"

    def test_code_cells(self, sample_notebook: Notebook) -> None:
        """Test code_cells property."""
        code_cells = sample_notebook.code_cells
        assert len(code_cells) == 2

    def test_markdown_cells(self, sample_notebook: Notebook) -> None:
        """Test markdown_cells property."""
        md_cells = sample_notebook.markdown_cells
        assert len(md_cells) == 1

    def test_cell_indices(self, sample_notebook: Notebook) -> None:
        """Test that cell indices are correct."""
        for i, cell in enumerate(sample_notebook):
            assert cell.index == i

    def test_cell_notebook_reference(self, sample_notebook: Notebook) -> None:
        """Test that cells have reference to parent notebook."""
        for cell in sample_notebook.cells:
            assert cell.notebook is sample_notebook


class TestNotebookConversion:
    @pytest.fixture
    def sample_notebook(self) -> Notebook:
        """Create a sample notebook."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                },
                {"cell_type": "markdown", "source": "# Title", "metadata": {}},
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        return Notebook.from_dict(data)

    def test_to_dict(self, sample_notebook: Notebook) -> None:
        """Test conversion to dictionary."""
        data = sample_notebook.to_dict()
        assert "cells" in data
        assert len(data["cells"]) == 2
        assert data["nbformat"] == 4

    def test_to_string_ipynb(self, sample_notebook: Notebook) -> None:
        """Test conversion to ipynb string."""
        content = sample_notebook.to_string(Format.IPYNB)
        data = json.loads(content)
        assert "cells" in data

    def test_to_string_percent(self, sample_notebook: Notebook) -> None:
        """Test conversion to percent format string."""
        content = sample_notebook.to_string(Format.PERCENT)
        assert "# %%" in content
        assert "def foo():" in content

    def test_to_file_ipynb(self, sample_notebook: Notebook, tmp_path: Path) -> None:
        """Test saving to ipynb file."""
        path = tmp_path / "output.ipynb"
        sample_notebook.to_file(path)

        assert path.exists()
        data = json.loads(path.read_text())
        assert "cells" in data

    def test_to_file_percent(self, sample_notebook: Notebook, tmp_path: Path) -> None:
        """Test saving to percent file."""
        path = tmp_path / "output.pct.py"
        sample_notebook.to_file(path)

        assert path.exists()
        content = path.read_text()
        assert "# %%" in content


class TestNotebookClean:
    def test_clean_removes_outputs(self) -> None:
        """Test clean removes cell outputs when requested."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "print(1)",
                    "metadata": {},
                    "outputs": [{"output_type": "stream", "name": "stdout", "text": "1"}],
                    "execution_count": 1,
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        nb = Notebook.from_dict(data)
        cleaned = nb.clean(remove_outputs=True)

        # Original unchanged
        assert len(nb.cells[0].outputs) == 1

        # Cleaned has no outputs
        assert len(cleaned.cells[0].outputs) == 0

    def test_clean_vcs_defaults(self) -> None:
        """Test clean uses VCS-friendly defaults (based on for_vcs())."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "print(1)",
                    "metadata": {"scrolled": True},
                    "outputs": [{"output_type": "stream", "name": "stdout", "text": "1"}],
                    "execution_count": 1,
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        nb = Notebook.from_dict(data)
        cleaned = nb.clean()  # Uses VCS-friendly defaults

        # Outputs should be preserved (remove_outputs=False)
        assert len(cleaned.cells[0].outputs) == 1
        # Execution count should be removed (remove_execution_counts=True)
        assert cleaned.cells[0].execution_count is None
        # Cell metadata should be removed (remove_cell_metadata=True)
        assert cleaned.cells[0].metadata == {}


class TestFormat:
    def test_from_path_ipynb(self) -> None:
        """Test format detection for ipynb."""
        assert Format.from_path(Path("test.ipynb")) == Format.IPYNB

    def test_from_path_pct(self) -> None:
        """Test format detection for pct.py."""
        assert Format.from_path(Path("test.pct.py")) == Format.PERCENT

    def test_from_path_py_raises(self) -> None:
        """Test format detection for plain .py raises FormatError."""
        # Plain .py files are not recognized as a notebook format by notebookx
        # Only .pct.py files are recognized as percent format
        from nblite.core.notebook import FormatError

        with pytest.raises(FormatError):
            Format.from_path(Path("test.py"))

    def test_from_extension(self) -> None:
        """Test format from extension."""
        assert Format.from_extension("ipynb") == Format.IPYNB
        assert Format.from_extension(".ipynb") == Format.IPYNB

    def test_from_extension_unknown_raises(self) -> None:
        """Test that unknown extensions raise FormatError."""
        from nblite.core.notebook import FormatError

        with pytest.raises(FormatError):
            Format.from_extension(".txt")

    def test_validate_valid_formats(self) -> None:
        """Test that valid formats pass validation."""
        assert Format.validate("ipynb") == "ipynb"
        assert Format.validate("percent") == "percent"

    def test_validate_invalid_format_raises(self) -> None:
        """Test that invalid formats raise FormatError."""
        from nblite.core.notebook import FormatError

        with pytest.raises(FormatError, match="Invalid format 'invalid'"):
            Format.validate("invalid")

    def test_to_notebookx_invalid_format_raises(self) -> None:
        """Test that to_notebookx raises FormatError for invalid formats."""
        from nblite.core.notebook import FormatError

        with pytest.raises(FormatError):
            Format.to_notebookx("invalid")


class TestNotebookRoundTrip:
    def test_ipynb_roundtrip(self, tmp_path: Path) -> None:
        """Test ipynb save and load preserves content."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        nb = Notebook.from_dict(data)

        path = tmp_path / "test.ipynb"
        nb.to_file(path)

        loaded = Notebook.from_file(path)
        assert len(loaded.cells) == len(nb.cells)
        assert loaded.cells[0].has_directive("export")

    def test_percent_roundtrip(self, tmp_path: Path) -> None:
        """Test percent format save and load."""
        data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        nb = Notebook.from_dict(data)

        path = tmp_path / "test.pct.py"
        nb.to_file(path)

        loaded = Notebook.from_file(path)
        assert len(loaded.cells) >= 1
        # Check that the directive is preserved
        assert any(cell.has_directive("export") for cell in loaded.cells)


class TestNotebookRepr:
    def test_repr_with_path(self, tmp_path: Path) -> None:
        """Test repr with source path."""
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(
            json.dumps(
                {
                    "cells": [],
                    "metadata": {},
                    "nbformat": 4,
                    "nbformat_minor": 5,
                }
            )
        )
        nb = Notebook.from_file(nb_path)
        repr_str = repr(nb)
        assert "test.ipynb" in repr_str

    def test_repr_without_path(self) -> None:
        """Test repr without source path."""
        nb = Notebook.from_dict(
            {
                "cells": [],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        repr_str = repr(nb)
        assert "None" in repr_str

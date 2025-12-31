"""
Tests for the CodeLocation class (Milestone 5).
"""

import json
from pathlib import Path

from nblite.config.schema import CodeLocationFormat, ExportMode
from nblite.core.code_location import CodeLocation


class TestCodeLocationCreation:
    def test_create_ipynb_location(self, tmp_path: Path) -> None:
        """Test creating ipynb code location."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        cl = CodeLocation(
            key="nbs",
            path=nbs_dir,
            format=CodeLocationFormat.IPYNB,
            export_mode=ExportMode.PERCENT,
        )
        assert cl.key == "nbs"
        assert cl.path == nbs_dir
        assert cl.format == CodeLocationFormat.IPYNB
        assert cl.file_ext == ".ipynb"
        assert cl.is_notebook is True

    def test_create_percent_location(self, tmp_path: Path) -> None:
        """Test creating percent code location."""
        pts_dir = tmp_path / "pts"
        pts_dir.mkdir()
        cl = CodeLocation(
            key="pts",
            path=pts_dir,
            format=CodeLocationFormat.PERCENT,
            export_mode=ExportMode.PERCENT,
        )
        assert cl.file_ext == ".pct.py"
        assert cl.is_notebook is True

    def test_create_module_location(self, tmp_path: Path) -> None:
        """Test creating module code location."""
        lib_dir = tmp_path / "mypackage"
        lib_dir.mkdir()
        cl = CodeLocation(
            key="lib",
            path=lib_dir,
            format=CodeLocationFormat.MODULE,
            export_mode=ExportMode.PERCENT,
        )
        assert cl.file_ext == ".py"
        assert cl.is_notebook is False

    def test_create_with_string_format(self, tmp_path: Path) -> None:
        """Test creating code location with string format."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        cl = CodeLocation(
            key="nbs",
            path=nbs_dir,
            format="ipynb",  # String format
        )
        assert cl.format == CodeLocationFormat.IPYNB

    def test_create_with_string_export_mode(self, tmp_path: Path) -> None:
        """Test creating code location with string export mode."""
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        cl = CodeLocation(
            key="lib",
            path=lib_dir,
            format="module",
            export_mode="py",  # String export mode
        )
        assert cl.export_mode == ExportMode.PY


class TestCodeLocationProperties:
    def test_relative_path_with_project_root(self, tmp_path: Path) -> None:
        """Test relative_path with project root."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        cl = CodeLocation(
            key="nbs",
            path=nbs_dir,
            format="ipynb",
            project_root=tmp_path,
        )
        assert cl.relative_path == Path("nbs")

    def test_relative_path_without_project_root(self, tmp_path: Path) -> None:
        """Test relative_path without project root."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        cl = CodeLocation(
            key="nbs",
            path=nbs_dir,
            format="ipynb",
        )
        assert cl.relative_path == nbs_dir


class TestCodeLocationGetFiles:
    def test_get_files(self, tmp_path: Path) -> None:
        """Test getting files from code location."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        (nbs_dir / "utils.ipynb").write_text("{}")
        (nbs_dir / "api.ipynb").write_text("{}")
        (nbs_dir / "__init__.ipynb").write_text("{}")
        (nbs_dir / ".hidden.ipynb").write_text("{}")

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb")
        files = cl.get_files()

        assert len(files) == 2
        assert all(not f.name.startswith("__") for f in files)
        assert all(not f.name.startswith(".") for f in files)

    def test_get_files_include_dunders(self, tmp_path: Path) -> None:
        """Test getting files including dunder files."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        (nbs_dir / "utils.ipynb").write_text("{}")
        (nbs_dir / "__init__.ipynb").write_text("{}")

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb")
        files = cl.get_files(ignore_dunders=False)

        assert len(files) == 2

    def test_get_files_include_hidden(self, tmp_path: Path) -> None:
        """Test getting files including hidden files."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        (nbs_dir / "utils.ipynb").write_text("{}")
        (nbs_dir / ".hidden.ipynb").write_text("{}")

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb")
        files = cl.get_files(ignore_hidden=False)

        assert len(files) == 2

    def test_get_files_nested(self, tmp_path: Path) -> None:
        """Test getting files from nested directories."""
        nbs_dir = tmp_path / "nbs"
        (nbs_dir / "api").mkdir(parents=True)
        (nbs_dir / "utils.ipynb").write_text("{}")
        (nbs_dir / "api" / "routes.ipynb").write_text("{}")

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb")
        files = cl.get_files()

        assert len(files) == 2

    def test_get_files_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test getting files from nonexistent directory."""
        cl = CodeLocation(
            key="nbs",
            path=tmp_path / "nonexistent",
            format="ipynb",
        )
        files = cl.get_files()
        assert len(files) == 0

    def test_get_files_percent_format(self, tmp_path: Path) -> None:
        """Test getting files with percent format."""
        pts_dir = tmp_path / "pts"
        pts_dir.mkdir()
        (pts_dir / "utils.pct.py").write_text("# %% test")
        (pts_dir / "api.pct.py").write_text("# %% test")
        (pts_dir / "other.py").write_text("def foo(): pass")  # Should be ignored

        cl = CodeLocation(key="pts", path=pts_dir, format="percent")
        files = cl.get_files()

        assert len(files) == 2
        assert all(f.name.endswith(".pct.py") for f in files)


class TestCodeLocationGetNotebooks:
    def test_get_notebooks(self, tmp_path: Path) -> None:
        """Test getting notebooks from code location."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()

        # Create valid ipynb file
        nb_content = json.dumps(
            {
                "cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "utils.ipynb").write_text(nb_content)

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb")
        notebooks = cl.get_notebooks()

        assert len(notebooks) == 1
        assert notebooks[0].code_location == "nbs"

    def test_get_notebooks_module_format_returns_empty(self, tmp_path: Path) -> None:
        """Test that get_notebooks returns empty for module format."""
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        (lib_dir / "utils.py").write_text("def foo(): pass")

        cl = CodeLocation(key="lib", path=lib_dir, format="module")
        notebooks = cl.get_notebooks()

        assert len(notebooks) == 0


class TestCodeLocationRepr:
    def test_repr(self, tmp_path: Path) -> None:
        """Test repr output."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb")
        repr_str = repr(cl)
        assert "nbs" in repr_str
        assert "ipynb" in repr_str

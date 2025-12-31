"""
Tests for the fill module (notebook execution and output filling).
"""

import json
from pathlib import Path

from nblite.core.notebook import Notebook
from nblite.fill import (
    HASH_METADATA_KEY,
    FillStatus,
    fill_notebook,
    fill_notebooks,
    get_notebook_hash,
    get_notebook_hash_from_path,
    has_notebook_changed,
)


def create_simple_notebook(
    tmp_path: Path, name: str = "test.ipynb", cells: list | None = None
) -> Path:
    """Create a simple notebook file for testing."""
    if cells is None:
        cells = [
            {
                "cell_type": "code",
                "source": "x = 1 + 1\nprint(x)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ]

    nb_content = {
        "cells": cells,
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    path = tmp_path / name
    path.write_text(json.dumps(nb_content))
    return path


class TestHashFunctions:
    """Tests for hash calculation and comparison."""

    def test_get_notebook_hash_basic(self, tmp_path: Path) -> None:
        """Test basic hash calculation."""
        path = create_simple_notebook(tmp_path)
        nb = Notebook.from_file(path)

        hash_value = get_notebook_hash(nb)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex digest

    def test_get_notebook_hash_consistent(self, tmp_path: Path) -> None:
        """Test that hash is consistent for same content."""
        path = create_simple_notebook(tmp_path)
        nb = Notebook.from_file(path)

        hash1 = get_notebook_hash(nb)
        hash2 = get_notebook_hash(nb)

        assert hash1 == hash2

    def test_get_notebook_hash_changes_with_source(self, tmp_path: Path) -> None:
        """Test that hash changes when source changes."""
        path1 = create_simple_notebook(
            tmp_path,
            "test1.ipynb",
            cells=[
                {
                    "cell_type": "code",
                    "source": "x = 1",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            ],
        )
        path2 = create_simple_notebook(
            tmp_path,
            "test2.ipynb",
            cells=[
                {
                    "cell_type": "code",
                    "source": "x = 2",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            ],
        )

        nb1 = Notebook.from_file(path1)
        nb2 = Notebook.from_file(path2)

        hash1 = get_notebook_hash(nb1)
        hash2 = get_notebook_hash(nb2)

        assert hash1 != hash2

    def test_get_notebook_hash_from_path(self, tmp_path: Path) -> None:
        """Test hash calculation from path."""
        path = create_simple_notebook(tmp_path)

        hash_value, has_changed = get_notebook_hash_from_path(path)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
        assert has_changed is True  # No hash stored yet

    def test_has_notebook_changed_no_hash(self, tmp_path: Path) -> None:
        """Test that notebook without hash is considered changed."""
        path = create_simple_notebook(tmp_path)
        nb = Notebook.from_file(path)

        assert has_notebook_changed(nb) is True

    def test_has_notebook_changed_with_matching_hash(self, tmp_path: Path) -> None:
        """Test that notebook with matching hash is not considered changed."""
        path = create_simple_notebook(tmp_path)
        nb = Notebook.from_file(path)

        # Calculate hash and store it in metadata
        hash_value = get_notebook_hash(nb)
        nb_dict = nb.to_dict()
        nb_dict["metadata"][HASH_METADATA_KEY] = hash_value

        # Write back
        path.write_text(json.dumps(nb_dict))
        nb = Notebook.from_file(path)

        assert has_notebook_changed(nb) is False

    def test_has_notebook_changed_with_wrong_hash(self, tmp_path: Path) -> None:
        """Test that notebook with wrong hash is considered changed."""
        path = create_simple_notebook(tmp_path)
        nb = Notebook.from_file(path)

        # Store wrong hash
        nb_dict = nb.to_dict()
        nb_dict["metadata"][HASH_METADATA_KEY] = "wrong_hash_value"

        path.write_text(json.dumps(nb_dict))
        nb = Notebook.from_file(path)

        assert has_notebook_changed(nb) is True


class TestFillNotebook:
    """Tests for single notebook execution."""

    def test_fill_simple_notebook(self, tmp_path: Path) -> None:
        """Test filling a simple notebook."""
        path = create_simple_notebook(tmp_path)

        result = fill_notebook(path)

        assert result.status == FillStatus.SUCCESS
        assert result.path == path

        # Check that notebook was filled
        nb_data = json.loads(path.read_text())
        code_cell = nb_data["cells"][0]
        assert code_cell["outputs"]  # Should have output now
        assert HASH_METADATA_KEY in nb_data["metadata"]

    def test_fill_notebook_dry_run(self, tmp_path: Path) -> None:
        """Test dry run doesn't modify notebook."""
        path = create_simple_notebook(tmp_path)
        original_content = path.read_text()

        result = fill_notebook(path, dry_run=True)

        assert result.status == FillStatus.SUCCESS
        assert path.read_text() == original_content

    def test_fill_notebook_removes_outputs_first(self, tmp_path: Path) -> None:
        """Test remove_outputs_first option."""
        cells = [
            {
                "cell_type": "code",
                "source": "x = 1\nprint(x)",
                "metadata": {},
                "outputs": [{"output_type": "stream", "name": "stdout", "text": "old output"}],
                "execution_count": 99,
            }
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path, remove_outputs_first=True)

        assert result.status == FillStatus.SUCCESS

        nb_data = json.loads(path.read_text())
        code_cell = nb_data["cells"][0]
        # Output should be the new one (containing "1"), not the old one
        assert any("1" in str(o) for o in code_cell["outputs"])

    def test_fill_notebook_with_timeout(self, tmp_path: Path) -> None:
        """Test timeout option."""
        cells = [
            {
                "cell_type": "code",
                "source": "x = 1",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path, timeout=60)

        assert result.status == FillStatus.SUCCESS

    def test_fill_notebook_with_error(self, tmp_path: Path) -> None:
        """Test handling execution errors."""
        cells = [
            {
                "cell_type": "code",
                "source": "raise ValueError('test error')",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path)

        assert result.status == FillStatus.ERROR
        assert result.error is not None

    def test_fill_notebook_stores_hash(self, tmp_path: Path) -> None:
        """Test that fill stores the hash in metadata."""
        path = create_simple_notebook(tmp_path)

        fill_notebook(path)

        nb_data = json.loads(path.read_text())
        assert HASH_METADATA_KEY in nb_data["metadata"]
        assert len(nb_data["metadata"][HASH_METADATA_KEY]) == 64

    def test_fill_notebook_from_notebook_object(self, tmp_path: Path) -> None:
        """Test filling using Notebook object."""
        path = create_simple_notebook(tmp_path)
        nb = Notebook.from_file(path)

        result = fill_notebook(nb)

        assert result.status == FillStatus.SUCCESS


class TestSkipDirectives:
    """Tests for skip directives (#|eval: false, #|skip_evals, etc.)."""

    def test_skip_eval_false(self, tmp_path: Path) -> None:
        """Test #|eval: false directive."""
        cells = [
            {
                "cell_type": "code",
                "source": "#|eval: false\nraise ValueError('should not execute')",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "source": "x = 1\nprint(x)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path)

        assert result.status == FillStatus.SUCCESS

        # First cell should not have outputs (was skipped)
        nb_data = json.loads(path.read_text())
        assert len(nb_data["cells"][0]["outputs"]) == 0
        # Second cell should have outputs
        assert len(nb_data["cells"][1]["outputs"]) > 0

    def test_skip_evals_block(self, tmp_path: Path) -> None:
        """Test #|skip_evals and #|skip_evals_stop block."""
        cells = [
            {
                "cell_type": "code",
                "source": "y = 1\nprint(y)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "source": "#|skip_evals\nraise ValueError('should not execute')",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "source": "raise ValueError('also should not execute')",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "source": "#|skip_evals_stop\nz = 2\nprint(z)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "source": "w = 3\nprint(w)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path)

        assert result.status == FillStatus.SUCCESS

        nb_data = json.loads(path.read_text())
        # Cell 0 should have output (before skip_evals)
        assert len(nb_data["cells"][0]["outputs"]) > 0
        # Cells 1-2 should have no output (in skip block)
        assert len(nb_data["cells"][1]["outputs"]) == 0
        assert len(nb_data["cells"][2]["outputs"]) == 0
        # Cell 3 (#|skip_evals_stop) DOES execute - skip mode ends at directive
        assert len(nb_data["cells"][3]["outputs"]) > 0
        # Cell 4 should have output (after skip_evals_stop)
        assert len(nb_data["cells"][4]["outputs"]) > 0

    def test_nested_skip_evals_raises(self, tmp_path: Path) -> None:
        """Test that nested #|skip_evals raises error."""
        cells = [
            {
                "cell_type": "code",
                "source": "#|skip_evals\nx = 1",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "source": "#|skip_evals\ny = 2",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path)

        assert result.status == FillStatus.ERROR
        assert "Already in skip_evals mode" in str(result.error)

    def test_skip_evals_stop_without_start_raises(self, tmp_path: Path) -> None:
        """Test that #|skip_evals_stop without #|skip_evals raises error."""
        cells = [
            {
                "cell_type": "code",
                "source": "#|skip_evals_stop\nx = 1",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
        ]
        path = create_simple_notebook(tmp_path, cells=cells)

        result = fill_notebook(path)

        assert result.status == FillStatus.ERROR
        assert "Not in skip_evals mode" in str(result.error)


class TestFillNotebooks:
    """Tests for batch notebook execution."""

    def test_fill_multiple_notebooks(self, tmp_path: Path) -> None:
        """Test filling multiple notebooks."""
        paths = [create_simple_notebook(tmp_path, f"nb{i}.ipynb") for i in range(3)]

        results = fill_notebooks(paths, skip_unchanged=False)

        assert len(results) == 3
        assert all(r.status == FillStatus.SUCCESS for r in results)

    def test_fill_notebooks_skip_unchanged(self, tmp_path: Path) -> None:
        """Test skip_unchanged option."""
        # Create and fill a notebook
        path = create_simple_notebook(tmp_path)
        fill_notebook(path)  # This stores the hash

        # Try to fill again with skip_unchanged
        results = fill_notebooks([path], skip_unchanged=True)

        assert len(results) == 1
        assert results[0].status == FillStatus.SKIPPED

    def test_fill_notebooks_with_progress(self, tmp_path: Path) -> None:
        """Test progress callback."""
        paths = [create_simple_notebook(tmp_path, f"nb{i}.ipynb") for i in range(2)]

        progress_calls = []

        def on_progress(path, result):
            progress_calls.append((path, result.status))

        fill_notebooks(paths, skip_unchanged=False, on_progress=on_progress)

        assert len(progress_calls) == 2

    def test_fill_notebooks_parallel(self, tmp_path: Path) -> None:
        """Test parallel execution."""
        paths = [create_simple_notebook(tmp_path, f"nb{i}.ipynb") for i in range(4)]

        results = fill_notebooks(paths, n_workers=2, skip_unchanged=False)

        assert len(results) == 4
        assert all(r.status == FillStatus.SUCCESS for r in results)

    def test_fill_notebooks_dry_run(self, tmp_path: Path) -> None:
        """Test batch dry run."""
        paths = [create_simple_notebook(tmp_path, f"nb{i}.ipynb") for i in range(2)]
        original_contents = [p.read_text() for p in paths]

        results = fill_notebooks(paths, dry_run=True, skip_unchanged=False)

        assert all(r.status == FillStatus.SUCCESS for r in results)
        # Files should not be modified
        for path, original in zip(paths, original_contents, strict=True):
            assert path.read_text() == original


class TestFillConfig:
    """Tests for fill configuration in nblite.toml."""

    def test_fill_config_default_values(self) -> None:
        """Test FillConfig default values."""
        from nblite.config.schema import FillConfig

        config = FillConfig()

        assert config.timeout is None
        assert config.n_workers == 4
        assert config.skip_unchanged is True
        assert config.remove_outputs_first is False
        assert config.code_locations is None
        assert config.exclude_patterns == []
        assert config.exclude_dunders is True
        assert config.exclude_hidden is True

    def test_fill_config_custom_values(self) -> None:
        """Test FillConfig with custom values."""
        from nblite.config.schema import FillConfig

        config = FillConfig(
            timeout=120,
            n_workers=8,
            skip_unchanged=False,
            remove_outputs_first=True,
            code_locations=["nbs"],
            exclude_patterns=["test_*.ipynb"],
            exclude_dunders=False,
            exclude_hidden=False,
        )

        assert config.timeout == 120
        assert config.n_workers == 8
        assert config.skip_unchanged is False
        assert config.remove_outputs_first is True
        assert config.code_locations == ["nbs"]
        assert config.exclude_patterns == ["test_*.ipynb"]
        assert config.exclude_dunders is False
        assert config.exclude_hidden is False

    def test_fill_config_in_nblite_config(self) -> None:
        """Test fill config is part of NbliteConfig."""
        from nblite.config.schema import NbliteConfig

        config = NbliteConfig()

        assert hasattr(config, "fill")
        assert config.fill.n_workers == 4


class TestFillCLI:
    """Tests for fill CLI command."""

    def test_fill_command_exists(self) -> None:
        """Test that fill command is registered."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["fill", "--help"])

        assert result.exit_code == 0
        assert "fill" in result.output.lower() or "execute" in result.output.lower()

    def test_test_command_exists(self) -> None:
        """Test that test command is registered."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["test", "--help"])

        assert result.exit_code == 0

    def test_fill_cli_with_notebooks(self, tmp_path: Path) -> None:
        """Test fill CLI with specific notebooks."""
        import os

        from typer.testing import CliRunner

        from nblite.cli.app import app

        # Create nblite.toml
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        # Create a simple notebook
        path = create_simple_notebook(nbs_dir)

        runner = CliRunner()
        # Change to project directory for CLI
        result = runner.invoke(app, ["fill", str(path)], env={"PWD": str(tmp_path)})

        # Run from the project directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["fill", str(path)])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"

    def test_fill_cli_dry_run(self, tmp_path: Path) -> None:
        """Test fill CLI with --dry-run option."""
        import os

        from typer.testing import CliRunner

        from nblite.cli.app import app

        # Create nblite.toml
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        path = create_simple_notebook(nbs_dir)
        original_content = path.read_text()

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["fill", "--dry-run", str(path)])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # File should not be modified
        assert path.read_text() == original_content

    def test_test_cli_is_dry_run(self, tmp_path: Path) -> None:
        """Test that 'test' command is equivalent to 'fill --dry-run'."""
        import os

        from typer.testing import CliRunner

        from nblite.cli.app import app

        # Create nblite.toml
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        path = create_simple_notebook(nbs_dir)
        original_content = path.read_text()

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["test", str(path)])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # File should not be modified (dry_run)
        assert path.read_text() == original_content

    def test_fill_cli_disables_export_by_default(self, tmp_path: Path) -> None:
        """Test that fill CLI disables nbl_export() by default."""
        import os

        from nblite import DISABLE_NBLITE_EXPORT_ENV_VAR

        # Create nblite.toml
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        # Create a notebook that checks the env var
        import json

        nb_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": f"import os\nresult = os.environ.get('{DISABLE_NBLITE_EXPORT_ENV_VAR}', '')",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        path = nbs_dir / "check_env.ipynb"
        path.write_text(json.dumps(nb_content))

        # Run fill (which should set the env var)
        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["fill", str(path)])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # After fill, the env var should be restored
        assert os.environ.get(DISABLE_NBLITE_EXPORT_ENV_VAR) is None

    def test_fill_cli_allow_export_option(self, tmp_path: Path) -> None:
        """Test that --allow-export flag enables nbl_export() during fill."""
        import os

        from nblite import DISABLE_NBLITE_EXPORT_ENV_VAR

        # Create nblite.toml
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        path = create_simple_notebook(nbs_dir)

        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # With --allow-export, the env var should NOT be set
            result = runner.invoke(app, ["fill", "--allow-export", str(path)])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # Env var should not be set after fill completes
        assert os.environ.get(DISABLE_NBLITE_EXPORT_ENV_VAR) is None


class TestFillIntegration:
    """Integration tests for fill with project structure."""

    def test_fill_with_project(self, tmp_path: Path) -> None:
        """Test fill with a full project setup."""
        # Create project structure
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()

        # Create nblite.toml
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"

[fill]
timeout = 60
n_workers = 1
skip_unchanged = true
"""
        (tmp_path / "nblite.toml").write_text(config)

        # Create a notebook
        create_simple_notebook(nbs_dir, "test.ipynb")

        # Load project and verify config
        from nblite.core import NbliteProject

        project = NbliteProject.from_path(tmp_path)

        assert project.config.fill.timeout == 60
        assert project.config.fill.n_workers == 1
        assert project.config.fill.skip_unchanged is True

    def test_fill_excludes_dunders(self, tmp_path: Path) -> None:
        """Test that __* notebooks are excluded by default."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()

        # Create notebooks
        regular_path = create_simple_notebook(nbs_dir, "regular.ipynb")
        dunder_path = create_simple_notebook(nbs_dir, "__init__.ipynb")

        # Both should exist
        assert regular_path.exists()
        assert dunder_path.exists()

        # Fill with exclude_dunders (default behavior)
        # The dunder notebook should be skipped in get_notebooks

    def test_fill_excludes_hidden(self, tmp_path: Path) -> None:
        """Test that .* notebooks are excluded by default."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()

        # Create notebooks
        regular_path = create_simple_notebook(nbs_dir, "regular.ipynb")
        hidden_path = create_simple_notebook(nbs_dir, ".hidden.ipynb")

        assert regular_path.exists()
        assert hidden_path.exists()

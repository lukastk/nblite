"""
Integration tests for the --python option with actual virtual environments.

These tests create real venvs using uv and verify that notebook execution
uses the correct Python binary.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _uv_available() -> bool:
    """Check if uv is available on the system."""
    return shutil.which("uv") is not None


@pytest.fixture
def venv_with_ipykernel(tmp_path: Path):
    """
    Create a virtual environment with ipykernel installed using uv.

    Yields the path to the Python binary in the venv.
    """
    if not _uv_available():
        pytest.skip("uv is not available")

    venv_dir = tmp_path / "test_venv"

    # Create venv
    result = subprocess.run(
        ["uv", "venv", str(venv_dir), "--python", sys.executable],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(f"Failed to create venv: {result.stderr}")

    python_path = venv_dir / "bin" / "python"
    if not python_path.exists():
        # Windows
        python_path = venv_dir / "Scripts" / "python.exe"

    if not python_path.exists():
        pytest.skip("Could not find python in venv")

    # Install ipykernel
    result = subprocess.run(
        ["uv", "pip", "install", "ipykernel", "--python", str(python_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.skip(f"Failed to install ipykernel: {result.stderr}")

    # Verify ipykernel is actually importable
    verify = subprocess.run(
        [str(python_path), "-c", "import ipykernel"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if verify.returncode != 0:
        pytest.skip(f"ipykernel not importable after install: {verify.stderr}")

    yield python_path


def create_notebook_that_prints_executable(path: Path) -> Path:
    """Create a notebook that prints sys.executable to stdout."""
    nb_content = {
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-0",
                "source": "import sys\nprint(sys.executable)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb_content))
    return path


def create_simple_notebook(path: Path) -> Path:
    """Create a simple notebook for testing."""
    nb_content = {
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-0",
                "source": "x = 1 + 1\nprint(x)",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb_content))
    return path


class TestFillNotebookWithVenvPython:
    """Test fill_notebook with a venv Python binary."""

    def test_fill_notebook_with_venv_python(self, tmp_path: Path, venv_with_ipykernel: Path) -> None:
        """Test that fill_notebook uses the specified Python binary."""
        from nblite.fill import fill_notebook, FillStatus

        nb_path = create_notebook_that_prints_executable(tmp_path / "test.ipynb")

        result = fill_notebook(nb_path, python=venv_with_ipykernel)

        assert result.status == FillStatus.SUCCESS

        # Check that the output contains the venv python path
        nb_data = json.loads(nb_path.read_text())
        outputs = nb_data["cells"][0]["outputs"]
        assert len(outputs) > 0
        # Stream output text can be a string or list of strings
        raw_text = outputs[0].get("text", "")
        output_text = "".join(raw_text) if isinstance(raw_text, list) else raw_text
        # The venv python should be within the venv dir
        venv_dir = str(venv_with_ipykernel.parent.parent)
        assert venv_dir in output_text or str(venv_with_ipykernel) in output_text

    def test_fill_notebooks_batch_with_venv(self, tmp_path: Path, venv_with_ipykernel: Path) -> None:
        """Test batch fill_notebooks with a venv Python."""
        from nblite.fill import fill_notebooks, FillStatus

        paths = [
            create_simple_notebook(tmp_path / f"nb{i}.ipynb")
            for i in range(2)
        ]

        results = fill_notebooks(
            paths,
            skip_unchanged=False,
            python=venv_with_ipykernel,
        )

        assert len(results) == 2
        assert all(r.status == FillStatus.SUCCESS for r in results)

    def test_fill_notebooks_parallel_with_venv(self, tmp_path: Path, venv_with_ipykernel: Path) -> None:
        """Test parallel fill_notebooks with a venv Python."""
        from nblite.fill import fill_notebooks, FillStatus

        paths = [
            create_simple_notebook(tmp_path / f"nb{i}.ipynb")
            for i in range(3)
        ]

        results = fill_notebooks(
            paths,
            skip_unchanged=False,
            n_workers=2,
            python=venv_with_ipykernel,
        )

        assert len(results) == 3
        assert all(r.status == FillStatus.SUCCESS for r in results)


class TestFillCLIWithPython:
    """Test CLI commands with --python option."""

    def test_fill_cli_with_python_option(self, tmp_path: Path, venv_with_ipykernel: Path) -> None:
        """Test nbl fill --python with a venv."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        # Set up project
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        nb_path = create_simple_notebook(nbs_dir / "test.ipynb")

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app, ["fill", "--python", str(venv_with_ipykernel), str(nb_path)]
            )
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"

    def test_test_cli_with_python_option(self, tmp_path: Path, venv_with_ipykernel: Path) -> None:
        """Test nbl test --python with a venv."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        # Set up project
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nblite.toml").write_text(config)

        nb_path = create_simple_notebook(nbs_dir / "test.ipynb")

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app, ["test", "--python", str(venv_with_ipykernel), str(nb_path)]
            )
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"

    def test_fill_config_python_in_toml(self, tmp_path: Path, venv_with_ipykernel: Path) -> None:
        """Test python specification via nblite.toml config."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        # Set up project with python in config
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        config = f"""
[cl.nbs]
path = "nbs"
format = "ipynb"

[fill]
python = "{venv_with_ipykernel}"
"""
        (tmp_path / "nblite.toml").write_text(config)

        nb_path = create_simple_notebook(nbs_dir / "test.ipynb")

        runner = CliRunner()
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["fill", str(nb_path)])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0, f"CLI failed: {result.output}"


class TestFillCLIPythonHelp:
    """Test that --python appears in CLI help."""

    def test_fill_python_option_in_help(self) -> None:
        """Test --python option appears in fill --help."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["fill", "--help"])

        assert result.exit_code == 0
        assert "--python" in result.output

    def test_test_python_option_in_help(self) -> None:
        """Test --python option appears in test --help."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["test", "--help"])

        assert result.exit_code == 0
        assert "--python" in result.output

    def test_prepare_python_option_in_help(self) -> None:
        """Test --python option appears in prepare --help."""
        from typer.testing import CliRunner

        from nblite.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["prepare", "--help"])

        assert result.exit_code == 0
        assert "--python" in result.output

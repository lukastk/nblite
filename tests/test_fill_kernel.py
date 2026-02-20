"""
Tests for the kernel spec utility module (nblite.fill.kernel).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nblite.fill.kernel import (
    CUSTOM_KERNEL_NAME,
    create_custom_kernel_spec,
    custom_kernel_environment,
    validate_python_binary,
)


def _has_ipykernel() -> bool:
    """Check if ipykernel is importable in the current Python."""
    result = subprocess.run(
        [sys.executable, "-c", "import ipykernel"],
        capture_output=True,
    )
    return result.returncode == 0


requires_ipykernel = pytest.mark.skipif(
    not _has_ipykernel(),
    reason="ipykernel not installed in current environment",
)


class TestValidatePythonBinary:
    """Tests for validate_python_binary."""

    @requires_ipykernel
    def test_validates_current_executable(self) -> None:
        """Test that the current Python executable passes validation."""
        result = validate_python_binary(sys.executable)
        assert result == Path(sys.executable).absolute()

    def test_rejects_nonexistent_path(self) -> None:
        """Test that a nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Python binary not found"):
            validate_python_binary("/nonexistent/path/python")

    def test_rejects_non_executable(self, tmp_path: Path) -> None:
        """Test that a non-executable file raises PermissionError."""
        fake_python = tmp_path / "fake_python"
        fake_python.write_text("not a real python")
        fake_python.chmod(0o444)  # readable but not executable

        with pytest.raises(PermissionError, match="not executable"):
            validate_python_binary(fake_python)

    def test_rejects_missing_ipykernel(self, tmp_path: Path) -> None:
        """Test that a Python without ipykernel raises RuntimeError."""
        # Create a script that fails on import ipykernel
        fake_python = tmp_path / "fake_python"
        fake_python.write_text('#!/bin/sh\necho "ModuleNotFoundError" >&2\nexit 1\n')
        fake_python.chmod(0o755)

        with pytest.raises(RuntimeError, match="ipykernel is not installed"):
            validate_python_binary(fake_python)

    @requires_ipykernel
    def test_returns_absolute_path(self) -> None:
        """Test that the returned path is absolute."""
        result = validate_python_binary(sys.executable)
        assert result.is_absolute()


class TestCreateCustomKernelSpec:
    """Tests for create_custom_kernel_spec."""

    def test_creates_kernel_json(self, tmp_path: Path) -> None:
        """Test that kernel.json is created with correct structure."""
        kernel_name = create_custom_kernel_spec(sys.executable, tmp_path)

        assert kernel_name == CUSTOM_KERNEL_NAME

        kernel_json_path = tmp_path / "kernels" / CUSTOM_KERNEL_NAME / "kernel.json"
        assert kernel_json_path.exists()

        spec = json.loads(kernel_json_path.read_text())
        assert spec["argv"][0] == str(Path(sys.executable).absolute())
        assert spec["argv"][1:] == ["-m", "ipykernel_launcher", "-f", "{connection_file}"]
        assert spec["language"] == "python"
        assert "display_name" in spec

    def test_creates_directory_structure(self, tmp_path: Path) -> None:
        """Test that the directory structure is correctly created."""
        create_custom_kernel_spec(sys.executable, tmp_path)

        assert (tmp_path / "kernels").is_dir()
        assert (tmp_path / "kernels" / CUSTOM_KERNEL_NAME).is_dir()

    def test_overwrites_existing_spec(self, tmp_path: Path) -> None:
        """Test that calling twice doesn't fail."""
        create_custom_kernel_spec(sys.executable, tmp_path)
        create_custom_kernel_spec(sys.executable, tmp_path)

        kernel_json_path = tmp_path / "kernels" / CUSTOM_KERNEL_NAME / "kernel.json"
        assert kernel_json_path.exists()


@requires_ipykernel
class TestCustomKernelEnvironment:
    """Tests for custom_kernel_environment context manager."""

    def test_sets_jupyter_path(self) -> None:
        """Test that JUPYTER_PATH is set inside context."""
        old_jupyter_path = os.environ.get("JUPYTER_PATH")

        with custom_kernel_environment(sys.executable) as kernel_name:
            jupyter_path = os.environ.get("JUPYTER_PATH")
            assert jupyter_path is not None
            assert kernel_name == CUSTOM_KERNEL_NAME

            # Verify the temp dir in JUPYTER_PATH contains the kernel spec
            first_path = jupyter_path.split(os.pathsep)[0]
            kernel_json = Path(first_path) / "kernels" / CUSTOM_KERNEL_NAME / "kernel.json"
            assert kernel_json.exists()

        # After context, JUPYTER_PATH should be restored
        assert os.environ.get("JUPYTER_PATH") == old_jupyter_path

    def test_restores_jupyter_path_on_exit(self) -> None:
        """Test that JUPYTER_PATH is properly restored."""
        original = os.environ.get("JUPYTER_PATH")

        # Set a known value
        os.environ["JUPYTER_PATH"] = "/some/path"
        try:
            with custom_kernel_environment(sys.executable):
                # Should be prepended
                assert os.environ["JUPYTER_PATH"].endswith(f"{os.pathsep}/some/path")

            # Should be restored
            assert os.environ["JUPYTER_PATH"] == "/some/path"
        finally:
            # Restore original
            if original is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = original

    def test_cleans_up_temp_dir(self) -> None:
        """Test that the temp directory is cleaned up after context."""
        temp_dir_path = None

        with custom_kernel_environment(sys.executable):
            jupyter_path = os.environ["JUPYTER_PATH"]
            temp_dir_path = jupyter_path.split(os.pathsep)[0]
            assert Path(temp_dir_path).exists()

        # Temp dir should be cleaned up
        assert not Path(temp_dir_path).exists()

    def test_restores_on_exception(self) -> None:
        """Test that cleanup happens even on exception."""
        old_jupyter_path = os.environ.get("JUPYTER_PATH")
        temp_dir_path = None

        with pytest.raises(ValueError):
            with custom_kernel_environment(sys.executable):
                jupyter_path = os.environ["JUPYTER_PATH"]
                temp_dir_path = jupyter_path.split(os.pathsep)[0]
                raise ValueError("test error")

        # Should be cleaned up
        assert os.environ.get("JUPYTER_PATH") == old_jupyter_path
        assert not Path(temp_dir_path).exists()

    def test_yields_kernel_name(self) -> None:
        """Test that the context manager yields the correct kernel name."""
        with custom_kernel_environment(sys.executable) as kernel_name:
            assert kernel_name == CUSTOM_KERNEL_NAME

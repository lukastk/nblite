"""
Kernel spec utilities for custom Python binary execution.

Creates temporary Jupyter kernel specs pointing to a user-specified Python
binary, enabling notebook execution with specific Python environments.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

__all__ = [
    "validate_python_binary",
    "create_custom_kernel_spec",
    "custom_kernel_environment",
    "CUSTOM_KERNEL_NAME",
]

CUSTOM_KERNEL_NAME = "_nblite_custom"


def validate_python_binary(python: str | Path) -> Path:
    """
    Validate that a Python binary exists, is executable, and has ipykernel installed.

    Args:
        python: Path to the Python binary.

    Returns:
        Absolute Path to the Python binary (without resolving symlinks,
        to preserve virtual environment paths).

    Raises:
        FileNotFoundError: If the binary does not exist.
        PermissionError: If the binary is not executable.
        RuntimeError: If ipykernel is not installed in the target Python.
    """
    python_path = Path(python).absolute()

    if not python_path.exists():
        raise FileNotFoundError(f"Python binary not found: {python}")

    if not os.access(python_path, os.X_OK):
        raise PermissionError(f"Python binary is not executable: {python}")

    # Check that ipykernel is installed
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import ipykernel"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ipykernel is not installed in {python}. "
                f"Install it with: {python} -m pip install ipykernel"
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout checking ipykernel in {python}")

    return python_path


def create_custom_kernel_spec(python: str | Path, base_dir: str | Path) -> str:
    """
    Create a custom Jupyter kernel spec directory pointing to the given Python.

    Creates the directory structure:
        base_dir/kernels/_nblite_custom/kernel.json

    Args:
        python: Path to the Python binary.
        base_dir: Base directory for the kernel spec (will create kernels/ subdirectory).

    Returns:
        The kernel name (CUSTOM_KERNEL_NAME).
    """
    python_path = Path(python).absolute()
    base_dir = Path(base_dir)

    kernel_dir = base_dir / "kernels" / CUSTOM_KERNEL_NAME
    kernel_dir.mkdir(parents=True, exist_ok=True)

    kernel_spec = {
        "argv": [str(python_path), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "nblite custom Python",
        "language": "python",
    }

    kernel_json_path = kernel_dir / "kernel.json"
    kernel_json_path.write_text(json.dumps(kernel_spec, indent=2))

    return CUSTOM_KERNEL_NAME


@contextmanager
def custom_kernel_environment(python: str | Path):
    """
    Context manager that sets up a temporary kernel spec for a custom Python binary.

    Creates a temporary directory with a Jupyter kernel spec pointing to the
    given Python binary, and prepends it to JUPYTER_PATH so jupyter_client
    finds it. Cleans up on exit.

    Args:
        python: Path to the Python binary.

    Yields:
        The kernel name to use with ExecutePreprocessor.
    """
    python_path = validate_python_binary(python)

    tmp_dir = tempfile.mkdtemp(prefix="nblite_kernel_")
    try:
        kernel_name = create_custom_kernel_spec(python_path, tmp_dir)

        # Prepend to JUPYTER_PATH
        old_jupyter_path = os.environ.get("JUPYTER_PATH")
        if old_jupyter_path:
            os.environ["JUPYTER_PATH"] = f"{tmp_dir}{os.pathsep}{old_jupyter_path}"
        else:
            os.environ["JUPYTER_PATH"] = tmp_dir

        yield kernel_name
    finally:
        # Restore JUPYTER_PATH
        if old_jupyter_path is None:
            os.environ.pop("JUPYTER_PATH", None)
        else:
            os.environ["JUPYTER_PATH"] = old_jupyter_path

        # Clean up temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

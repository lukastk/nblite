"""
Convert Python modules to notebooks.

Provides functionality to convert existing Python files into
notebook format with appropriate directives.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

__all__ = ["module_to_notebook", "modules_to_notebooks"]


def module_to_notebook(
    module_path: Path | str,
    output_path: Path | str,
    *,
    module_name: str | None = None,
    format: str = "ipynb",
) -> None:
    """
    Convert a Python module to a notebook.

    Parses the Python file and creates a notebook with:
    - A default_exp directive
    - Code cells for each function/class
    - Markdown cells for module docstrings

    Args:
        module_path: Path to the Python module.
        output_path: Path for the output notebook.
        module_name: Module name for default_exp (default: file stem).
        format: Output format ("ipynb" or "percent").

    Example:
        >>> module_to_notebook("utils.py", "nbs/utils.ipynb", module_name="utils")
    """
    module_path = Path(module_path)
    output_path = Path(output_path)

    if not module_path.exists():
        raise FileNotFoundError(f"Module not found: {module_path}")

    source = module_path.read_text()

    # Determine module name
    if module_name is None:
        module_name = module_path.stem

    # Parse the Python file
    cells = _parse_module_to_cells(source, module_name)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "ipynb":
        _write_ipynb(output_path, cells)
    elif format == "percent":
        _write_percent(output_path, cells)
    else:
        raise ValueError(f"Unknown format: {format}")


def modules_to_notebooks(
    input_dir: Path | str,
    output_dir: Path | str,
    *,
    format: str = "ipynb",
    recursive: bool = True,
    exclude_init: bool = True,
    exclude_dunders: bool = True,
    exclude_hidden: bool = True,
) -> list[Path]:
    """
    Convert all Python modules in a directory to notebooks.

    Walks through the directory and converts each .py file to a notebook,
    preserving the directory structure.

    Args:
        input_dir: Path to the directory containing Python modules.
        output_dir: Path for the output notebooks directory.
        format: Output format ("ipynb" or "percent").
        recursive: Whether to process subdirectories.
        exclude_init: Whether to exclude __init__.py files.
        exclude_dunders: Whether to exclude __*.py files (like __main__.py).
        exclude_hidden: Whether to exclude hidden files/directories (starting with .).

    Returns:
        List of paths to created notebook files.

    Example:
        >>> modules_to_notebooks("mypackage/", "nbs/")
        [Path('nbs/core.ipynb'), Path('nbs/utils.ipynb'), ...]
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # Determine file extension for output
    if format == "ipynb":
        out_ext = ".ipynb"
    elif format == "percent":
        out_ext = ".pct.py"
    else:
        raise ValueError(f"Unknown format: {format}")

    created_files: list[Path] = []

    # Find all Python files
    pattern = "**/*.py" if recursive else "*.py"
    for py_file in input_dir.glob(pattern):
        # Skip excluded files
        if exclude_hidden and any(part.startswith(".") for part in py_file.parts):
            continue
        if exclude_dunders and py_file.name.startswith("__") and py_file.name != "__init__.py":
            continue
        if exclude_init and py_file.name == "__init__.py":
            continue

        # Skip __pycache__ directories
        if "__pycache__" in py_file.parts:
            continue

        # Calculate relative path and output path
        rel_path = py_file.relative_to(input_dir)
        out_path = output_dir / rel_path.with_suffix(out_ext)

        # Determine module name from relative path
        # e.g., "subdir/utils.py" -> "subdir.utils"
        parts = list(rel_path.parts)
        parts[-1] = rel_path.stem  # Remove .py extension
        module_name = ".".join(parts)

        # Convert the module
        module_to_notebook(py_file, out_path, module_name=module_name, format=format)
        created_files.append(out_path)

    return created_files


def _parse_module_to_cells(source: str, module_name: str) -> list[dict[str, Any]]:
    """Parse Python source into notebook cells."""
    cells: list[dict[str, Any]] = []

    # Add default_exp cell
    cells.append(
        {
            "cell_type": "code",
            "source": f"#|default_exp {module_name}",
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        }
    )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # If parsing fails, put everything in one cell
        cells.append(
            {
                "cell_type": "code",
                "source": f"#|export\n{source}",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        )
        return cells

    # Extract module docstring
    docstring = ast.get_docstring(tree)
    if docstring:
        cells.append(
            {
                "cell_type": "markdown",
                "source": f"# {module_name}\n\n{docstring}",
                "metadata": {},
            }
        )

    # Process imports first
    imports = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))

    if imports:
        import_source = "#|export\n" + "\n".join(imports)
        cells.append(
            {
                "cell_type": "code",
                "source": import_source,
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        )

    # Process functions and classes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            code = ast.unparse(node)
            cell_source = f"#|export\n{code}"

            cells.append(
                {
                    "cell_type": "code",
                    "source": cell_source,
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            )

    # If no functions/classes, put remaining code in one cell
    if len(cells) <= 2 and not imports:  # Only default_exp and maybe docstring
        remaining = []
        for node in tree.body:
            if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
                # Skip module docstring (which is an Expr)
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    continue
                remaining.append(ast.unparse(node))

        if remaining:
            cells.append(
                {
                    "cell_type": "code",
                    "source": "#|export\n" + "\n".join(remaining),
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            )

    return cells


def _write_ipynb(output_path: Path, cells: list[dict[str, Any]]) -> None:
    """Write cells as ipynb format."""
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    output_path.write_text(json.dumps(notebook, indent=2))


def _write_percent(output_path: Path, cells: list[dict[str, Any]]) -> None:
    """Write cells as percent format."""
    lines = []
    for cell in cells:
        if cell["cell_type"] == "code":
            lines.append("# %%")
            lines.append(cell["source"])
            lines.append("")
        elif cell["cell_type"] == "markdown":
            lines.append("# %% [markdown]")
            for line in cell["source"].split("\n"):
                lines.append(f"# {line}")
            lines.append("")

    output_path.write_text("\n".join(lines))

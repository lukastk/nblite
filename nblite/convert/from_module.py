"""
Convert Python modules to notebooks.

Provides functionality to convert existing Python files into
notebook format by treating them as single-cell notebooks with
export directives.
"""

from __future__ import annotations

from pathlib import Path

from nblite.core.notebook import Notebook

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

    Creates a notebook with the entire module source in a single code cell,
    with #|default_exp and #|export directives. This preserves all code
    exactly as written, including comments and formatting.

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

    # Create percent-format content with all source in one cell
    # This preserves everything: comments, formatting, all statements
    percent_content = f"# %%\n#|default_exp {module_name}\n#|export\n{source}"

    # Parse as percent format
    notebook = Notebook.from_string(percent_content, format="percent")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    notebook.to_file(output_path, format=format)


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

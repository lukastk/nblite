"""From-module command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console
from nblite.cli.app import app
from nblite.core.notebook import Notebook

__all__ = ["from_module_cmd", "module_to_notebook", "modules_to_notebooks"]


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


@app.command(name="from-module")
def from_module_cmd(
    input_path: Annotated[
        Path,
        typer.Argument(help="Path to Python module file or directory"),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(help="Output notebook path or directory"),
    ],
    module_name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Module name for default_exp (default: file stem). Only for single file.",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: ipynb or percent"),
    ] = "ipynb",
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive", "-r", help="Process subdirectories recursively (for directory input)"
        ),
    ] = True,
    include_init: Annotated[
        bool,
        typer.Option("--include-init", help="Include __init__.py files"),
    ] = False,
    include_dunders: Annotated[
        bool,
        typer.Option("--include-dunders", help="Include __*.py files (like __main__.py)"),
    ] = False,
    include_hidden: Annotated[
        bool,
        typer.Option("--include-hidden", help="Include hidden files/directories (starting with .)"),
    ] = False,
) -> None:
    """Convert Python module(s) to notebook(s).

    Can convert a single Python file or all Python files in a directory.

    Creates a notebook with the entire module source in a single code cell,
    with #|default_exp and #|export directives. This preserves all code
    exactly as written, including comments and formatting.

    For directory mode, converts all .py files while preserving directory structure.

    Example:
        nbl from-module utils.py nbs/utils.ipynb
        nbl from-module lib/core.py nbs/core.ipynb --name core
        nbl from-module src/ nbs/ --recursive
        nbl from-module mypackage/ notebooks/ --include-init
    """
    if not input_path.exists():
        console.print(f"[red]Error: Path not found: {input_path}[/red]")
        raise typer.Exit(1)

    if output_format not in ("ipynb", "percent"):
        console.print(
            f"[red]Error: Invalid format '{output_format}'. Use 'ipynb' or 'percent'.[/red]"
        )
        raise typer.Exit(1)

    try:
        if input_path.is_dir():
            # Directory mode
            if module_name is not None:
                console.print(
                    "[yellow]Warning: --name is ignored when converting a directory[/yellow]"
                )

            created = modules_to_notebooks(
                input_path,
                output_path,
                format=output_format,
                recursive=recursive,
                exclude_init=not include_init,
                exclude_dunders=not include_dunders,
                exclude_hidden=not include_hidden,
            )
            console.print(f"[green]Created {len(created)} notebook(s) in {output_path}[/green]")
            for path in created:
                console.print(f"  {path}")
        else:
            # Single file mode
            module_to_notebook(
                input_path,
                output_path,
                module_name=module_name,
                format=output_format,
            )
            console.print(f"[green]Created notebook: {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

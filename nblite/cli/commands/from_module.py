"""From-module command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from nblite.cli._helpers import console


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
        Optional[str],
        typer.Option("--name", "-n", help="Module name for default_exp (default: file stem). Only for single file."),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: ipynb or percent"),
    ] = "ipynb",
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Process subdirectories recursively (for directory input)"),
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

    For single file:
        Parses the Python file and creates a notebook with:
        - A default_exp directive
        - Code cells for imports
        - Code cells for each function/class with #|export directive
        - Markdown cells for module docstrings

    For directory:
        Converts all .py files, preserving directory structure.

    Example:
        nbl from-module utils.py nbs/utils.ipynb
        nbl from-module lib/core.py nbs/core.ipynb --name core
        nbl from-module src/ nbs/ --recursive
        nbl from-module mypackage/ notebooks/ --include-init
    """
    from nblite.convert import module_to_notebook, modules_to_notebooks

    if not input_path.exists():
        console.print(f"[red]Error: Path not found: {input_path}[/red]")
        raise typer.Exit(1)

    if output_format not in ("ipynb", "percent"):
        console.print(f"[red]Error: Invalid format '{output_format}'. Use 'ipynb' or 'percent'.[/red]")
        raise typer.Exit(1)

    try:
        if input_path.is_dir():
            # Directory mode
            if module_name is not None:
                console.print("[yellow]Warning: --name is ignored when converting a directory[/yellow]")

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
        raise typer.Exit(1)

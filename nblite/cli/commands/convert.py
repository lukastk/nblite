"""Convert command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console


def convert(
    input_path: Annotated[
        Path,
        typer.Argument(help="Input notebook path"),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(help="Output notebook path"),
    ],
    from_format: Annotated[
        str | None,
        typer.Option("--from", help="Input format (auto-detected if omitted)"),
    ] = None,
    to_format: Annotated[
        str | None,
        typer.Option("--to", help="Output format (auto-detected if omitted)"),
    ] = None,
) -> None:
    """Convert notebook between formats."""
    from nblite.core.notebook import Notebook
    from nblite.export.pipeline import export_notebook_to_notebook

    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input_path}[/red]")
        raise typer.Exit(1)

    nb = Notebook.from_file(input_path, format=from_format)
    export_notebook_to_notebook(nb, output_path, format=to_format)

    console.print(f"[green]Converted {input_path} -> {output_path}[/green]")

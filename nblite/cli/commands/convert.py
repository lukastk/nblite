"""Convert command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console
from nblite.cli.app import app
from nblite.core.notebook import Format


@app.command()
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
        typer.Option(
            "--from",
            help=f"Input format. Available formats: {', '.join(Format.get_valid_formats())}",
        ),
    ] = None,
    to_format: Annotated[
        str | None,
        typer.Option(
            "--to",
            help=f"Output format. Available formats: {', '.join(Format.get_valid_formats())}",
        ),
    ] = None,
) -> None:
    """Convert notebook between formats."""
    from nblite.core.notebook import FormatError, Notebook
    from nblite.export.pipeline import export_notebook_to_notebook

    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input_path}[/red]")
        raise typer.Exit(1)

    try:
        nb = Notebook.from_file(input_path, format=from_format)
        export_notebook_to_notebook(nb, output_path, format=to_format)
    except FormatError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]Converted {input_path} -> {output_path}[/green]")

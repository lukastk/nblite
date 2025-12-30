"""Export command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from nblite.cli._helpers import console, get_project


def export(
    ctx: typer.Context,
    notebooks: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Specific notebooks to export"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be exported without doing it"),
    ] = False,
) -> None:
    """Run the export pipeline."""
    project = get_project(ctx)

    if dry_run:
        console.print("[blue]Dry run - would export:[/blue]")
        nbs = project.get_notebooks()
        for nb in nbs:
            twins = project.get_notebook_twins(nb)
            console.print(f"  {nb.source_path}")
            for twin in twins:
                console.print(f"    -> {twin}")
        return

    result = project.export(notebooks=notebooks)

    if result.success:
        console.print("[green]Export completed successfully[/green]")
        for f in result.files_created:
            console.print(f"  [green]+[/green] {f}")
    else:
        console.print("[red]Export completed with errors[/red]")
        for error in result.errors:
            console.print(f"  [red]Error:[/red] {error}")
        raise typer.Exit(1)

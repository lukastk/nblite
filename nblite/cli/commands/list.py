"""List command for nblite CLI."""

from __future__ import annotations

from typing import Annotated

import typer

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command(name="list")
def list_files(
    ctx: typer.Context,
    code_location: Annotated[
        str | None,
        typer.Argument(help="Code location to list (all if omitted)"),
    ] = None,
) -> None:
    """List notebooks and files in the project."""
    project = get_project(ctx)

    locations = project.code_locations.values()
    if code_location:
        try:
            locations = [project.get_code_location(code_location)]
        except KeyError:
            console.print(f"[red]Unknown code location: {code_location}[/red]")
            raise typer.Exit(1) from None

    for cl in locations:
        console.print(f"[bold cyan]{cl.key}[/bold cyan] ({cl.relative_path}):")
        files = cl.get_files()
        for f in files:
            rel_path = f.relative_to(cl.path)
            console.print(f"  {rel_path}")
        if not files:
            console.print("  [dim](no files)[/dim]")
        console.print()

"""Info command for nblite CLI."""

from __future__ import annotations

import typer
from rich.table import Table

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command()
def info(ctx: typer.Context) -> None:
    """Show project information."""
    project = get_project(ctx)

    console.print(f"[bold]Project:[/bold] {project.root_path}")
    console.print()

    # Show code locations
    table = Table(title="Code Locations")
    table.add_column("Key", style="cyan")
    table.add_column("Path")
    table.add_column("Format")
    table.add_column("Files")

    for key, cl in project.code_locations.items():
        files = cl.get_files()
        table.add_row(
            key,
            str(cl.relative_path),
            cl.format.value,
            str(len(files)),
        )

    console.print(table)

    # Show export pipeline
    if project.config.export_pipeline:
        console.print()
        console.print("[bold]Export Pipeline:[/bold]")
        for rule in project.config.export_pipeline:
            console.print(f"  {rule.from_key} -> {rule.to_key}")

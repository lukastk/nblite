"""Readme command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command()
def readme(
    ctx: typer.Context,
    notebook_path: Annotated[
        Path | None,
        typer.Argument(help="Path to notebook (uses config readme_nb_path if omitted)"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path (default: README.md in project root)"),
    ] = None,
) -> None:
    """Generate README.md from a notebook.

    Converts the specified notebook to markdown, filtering out cells
    with #|hide directive. The notebook path can be specified on the
    command line or in nblite.toml as readme_nb_path.

    Example nblite.toml:
        readme_nb_path = "nbs/index.ipynb"
    """
    from nblite.readme import generate_readme

    project = get_project(ctx)

    # Determine notebook path
    if notebook_path is None:
        if project.config.readme_nb_path is None:
            console.print("[red]Error: No notebook specified.[/red]")
            console.print("Either pass a notebook path or set readme_nb_path in nblite.toml")
            raise typer.Exit(1)
        notebook_path = project.root_path / project.config.readme_nb_path
    else:
        if not notebook_path.is_absolute():
            notebook_path = project.root_path / notebook_path

    if not notebook_path.exists():
        console.print(f"[red]Error: Notebook not found: {notebook_path}[/red]")
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = project.root_path / "README.md"
    elif not output.is_absolute():
        output = project.root_path / output

    generate_readme(notebook_path, output)
    console.print(f"[green]Generated {output}[/green]")

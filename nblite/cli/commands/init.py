"""Init command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console
from nblite.cli.app import app


@app.command()
def init(
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Module name (default: directory name)"),
    ] = None,
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path (default: current directory)"),
    ] = None,
    use_defaults: Annotated[
        bool,
        typer.Option("--use-defaults", help="Use defaults without prompting"),
    ] = False,
) -> None:
    """Initialize a new nblite project."""
    project_path = path or Path.cwd()
    project_path = project_path.resolve()

    if name is None:
        name = project_path.name

    config_path = project_path / "nblite.toml"
    if config_path.exists() and not use_defaults:
        console.print("[yellow]nblite.toml already exists[/yellow]")
        raise typer.Exit(1)

    # Create default config
    config_content = f'''# nblite configuration
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "{name}"
format = "module"
'''

    # Create directories
    (project_path / "nbs").mkdir(exist_ok=True)
    (project_path / name).mkdir(exist_ok=True)
    (project_path / name / "__init__.py").touch()

    config_path.write_text(config_content)

    console.print(f"[green]Initialized nblite project: {name}[/green]")
    console.print(f"  Config: {config_path}")
    console.print(f"  Notebooks: {project_path / 'nbs'}")
    console.print(f"  Package: {project_path / name}")

"""
Main CLI application for nblite.

This module defines the `nbl` command and all subcommands.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from nblite import __version__

app = typer.Typer(
    name="nbl",
    help="nblite - Notebook-driven Python package development tool",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"nblite version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """nblite - Notebook-driven Python package development tool."""
    pass


@app.command()
def init(
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Module name (default: directory name)"),
    ] = None,
    path: Annotated[
        Optional[Path],
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


@app.command()
def new(
    notebook_path: Annotated[
        Path,
        typer.Argument(help="Path for the new notebook"),
    ],
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Module name for default_exp"),
    ] = None,
    title: Annotated[
        Optional[str],
        typer.Option("--title", "-t", help="Notebook title"),
    ] = None,
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template to use"),
    ] = None,
    no_export: Annotated[
        bool,
        typer.Option("--no-export", help="Don't include default_exp directive"),
    ] = False,
) -> None:
    """Create a new notebook."""
    from nblite.core.project import NbliteProject

    # Try to find project root
    try:
        project = NbliteProject.from_path()
        notebook_path = project.root_path / notebook_path
    except FileNotFoundError:
        notebook_path = Path.cwd() / notebook_path

    # Determine module name
    if name is None:
        name = notebook_path.stem
        if name.endswith(".pct"):
            name = name[:-4]

    # Create notebook content
    cells = []

    # Add default_exp directive
    if not no_export:
        cells.append({
            "cell_type": "code",
            "source": f"#|default_exp {name}",
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        })

    # Add title if specified
    if title:
        cells.append({
            "cell_type": "markdown",
            "source": f"# {title}",
            "metadata": {},
        })

    nb_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(nb_content, indent=2))

    console.print(f"[green]Created notebook: {notebook_path}[/green]")


@app.command()
def export(
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
    from nblite.core.project import NbliteProject

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

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


@app.command()
def clean(
    notebooks: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Specific notebooks to clean"),
    ] = None,
) -> None:
    """Clean notebooks by removing outputs and metadata."""
    from nblite.core.project import NbliteProject

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    project.clean(notebooks=notebooks)
    console.print("[green]Notebooks cleaned[/green]")


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
        Optional[str],
        typer.Option("--from", help="Input format (auto-detected if omitted)"),
    ] = None,
    to_format: Annotated[
        Optional[str],
        typer.Option("--to", help="Output format (auto-detected if omitted)"),
    ] = None,
) -> None:
    """Convert notebook between formats."""
    from nblite.core.notebook import Format, Notebook
    from nblite.export.pipeline import export_notebook_to_notebook

    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input_path}[/red]")
        raise typer.Exit(1)

    nb = Notebook.from_file(input_path, format=from_format)
    export_notebook_to_notebook(nb, output_path, format=to_format)

    console.print(f"[green]Converted {input_path} -> {output_path}[/green]")


@app.command()
def info() -> None:
    """Show project information."""
    from nblite.core.project import NbliteProject

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

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


@app.command("list")
def list_files(
    code_location: Annotated[
        Optional[str],
        typer.Argument(help="Code location to list (all if omitted)"),
    ] = None,
) -> None:
    """List notebooks and files in the project."""
    from nblite.core.project import NbliteProject

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    locations = project.code_locations.values()
    if code_location:
        try:
            locations = [project.get_code_location(code_location)]
        except KeyError:
            console.print(f"[red]Unknown code location: {code_location}[/red]")
            raise typer.Exit(1)

    for cl in locations:
        console.print(f"[bold cyan]{cl.key}[/bold cyan] ({cl.relative_path}):")
        files = cl.get_files()
        for f in files:
            rel_path = f.relative_to(cl.path)
            console.print(f"  {rel_path}")
        if not files:
            console.print("  [dim](no files)[/dim]")
        console.print()


@app.command("install-hooks")
def install_hooks_cmd() -> None:
    """Install git hooks for the project."""
    from nblite.core.project import NbliteProject
    from nblite.git.hooks import install_hooks

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    try:
        install_hooks(project)
        console.print("[green]Git hooks installed[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("uninstall-hooks")
def uninstall_hooks_cmd() -> None:
    """Remove git hooks for the project."""
    from nblite.core.project import NbliteProject
    from nblite.git.hooks import uninstall_hooks

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    uninstall_hooks(project)
    console.print("[green]Git hooks removed[/green]")


@app.command("validate")
def validate_cmd() -> None:
    """Validate git staging state."""
    from nblite.core.project import NbliteProject
    from nblite.git.staging import validate_staging

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    result = validate_staging(project)

    if result.warnings:
        for warning in result.warnings:
            console.print(f"[yellow]Warning:[/yellow] {warning}")

    if result.errors:
        for error in result.errors:
            console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(1)

    if result.valid and not result.warnings:
        console.print("[green]Staging is valid[/green]")


@app.command("hook")
def hook_cmd(
    hook_name: Annotated[
        str,
        typer.Argument(help="Hook name (pre-commit, post-commit)"),
    ],
) -> None:
    """Run a git hook (internal use)."""
    from nblite.core.project import NbliteProject

    try:
        project = NbliteProject.from_path()
    except FileNotFoundError:
        # Not in a project, silently exit
        return

    if hook_name == "pre-commit":
        # Auto-clean and validate
        if project.config.git.auto_clean:
            project.clean()

        if project.config.git.auto_export:
            project.export()

        if project.config.git.validate_staging:
            from nblite.git.staging import validate_staging
            result = validate_staging(project)
            if not result.valid:
                for error in result.errors:
                    console.print(f"[red]Error:[/red] {error}", err=True)
                raise typer.Exit(1)


if __name__ == "__main__":
    app()

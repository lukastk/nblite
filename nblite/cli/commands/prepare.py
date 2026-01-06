"""Prepare command for nblite CLI."""

from __future__ import annotations

from typing import Annotated

import typer

from nblite.cli._helpers import console, get_config_path, get_project
from nblite.cli.app import app
from nblite.cli.commands.fill import _run_fill


@app.command()
def prepare(
    ctx: typer.Context,
    skip_export: Annotated[
        bool,
        typer.Option("--skip-export", help="Skip export step"),
    ] = False,
    skip_clean: Annotated[
        bool,
        typer.Option("--skip-clean", help="Skip clean step"),
    ] = False,
    skip_fill: Annotated[
        bool,
        typer.Option("--skip-fill", help="Skip fill step"),
    ] = False,
    skip_readme: Annotated[
        bool,
        typer.Option("--skip-readme", help="Skip readme step"),
    ] = False,
    clean_outputs: Annotated[
        bool,
        typer.Option("--clean-outputs", help="Remove outputs during clean"),
    ] = False,
    fill_workers: Annotated[
        int,
        typer.Option("--fill-workers", "-w", help="Number of fill workers"),
    ] = 4,
    fill_unchanged: Annotated[
        bool,
        typer.Option("--fill-unchanged", help="Fill notebooks even if unchanged"),
    ] = False,
) -> None:
    """Run export, clean, fill, and readme in sequence.

    This is a convenience command that runs the full preparation
    pipeline for a project:
    1. Export notebooks (nbl export)
    2. Clean notebooks (nbl clean)
    3. Fill notebooks (nbl fill)
    4. Generate README (nbl readme) - only if readme_nb_path is configured

    Use --skip-* options to skip individual steps.
    """
    from nblite.readme import generate_readme

    project = get_project(ctx)
    config_path = get_config_path(ctx)

    # Step 1: Export
    if not skip_export:
        console.print("[bold]Step 1: Export[/bold]")
        result = project.export()
        if result.success:
            console.print(f"  [green]Exported {len(result.files_created)} files[/green]")
        else:
            console.print("[red]  Export failed[/red]")
            for error in result.errors:
                console.print(f"  [red]{error}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[dim]Step 1: Export (skipped)[/dim]")

    # Step 2: Clean
    if not skip_clean:
        console.print("[bold]Step 2: Clean[/bold]")
        project.clean(remove_outputs=clean_outputs if clean_outputs else None)
        console.print("  [green]Cleaned notebooks[/green]")
    else:
        console.print("[dim]Step 2: Clean (skipped)[/dim]")

    # Step 3: Fill
    if not skip_fill:
        console.print("[bold]Step 3: Fill[/bold]")
        exit_code = _run_fill(
            notebooks=None,
            code_locations=None,
            timeout=None,
            n_workers=fill_workers,
            fill_unchanged=fill_unchanged,
            remove_outputs_first=False,
            clean=True,
            save_hash=True,
            exclude_dunders=True,
            exclude_hidden=True,
            dry_run=False,
            silent=False,
            config_path=config_path,
        )
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        console.print("[dim]Step 3: Fill (skipped)[/dim]")

    # Step 4: README
    if not skip_readme and project.config.readme_nb_path:
        console.print("[bold]Step 4: README[/bold]")
        notebook_path = project.root_path / project.config.readme_nb_path
        if notebook_path.exists():
            output_path = project.root_path / "README.md"
            generate_readme(notebook_path, output_path)
            console.print(f"  [green]Generated {output_path}[/green]")
        else:
            console.print(f"  [yellow]Warning: readme notebook not found: {notebook_path}[/yellow]")
    elif skip_readme:
        console.print("[dim]Step 4: README (skipped)[/dim]")
    else:
        console.print("[dim]Step 4: README (no readme_nb_path configured)[/dim]")

    console.print()
    console.print("[green]Prepare completed![/green]")

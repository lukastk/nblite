"""Export command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command()
def export(
    ctx: typer.Context,
    notebooks: Annotated[
        list[Path] | None,
        typer.Argument(help="Specific notebooks to export"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be exported without doing it"),
    ] = False,
    export_pipeline: Annotated[
        str | None,
        typer.Option(
            "--pipeline",
            help="Custom export pipeline. E.g. 'nbs->lib' or 'pcts->nbs' (to reverse)",
        ),
    ] = None,
    reverse: Annotated[
        bool,
        typer.Option(
            "--reverse",
            "-r",
            help="Reverse the export pipeline direction (notebook formats only, excludes modules)",
        ),
    ] = False,
    silence_warnings: Annotated[
        bool,
        typer.Option(
            "--silence-warnings",
            help="Suppress warning messages about unrecognized directives",
        ),
    ] = False,
) -> None:
    """Run the export pipeline.

    By default, uses the export_pipeline defined in nblite.toml.
    Use --pipeline to override with a custom pipeline.
    Use --reverse to reverse the pipeline direction (excludes module code locations).

    The pipeline format is 'from -> to' where from and to are code location keys.
    Multiple rules can be comma-separated: 'nbs->pcts,pcts->lib'

    Example:
        nbl export
        nbl export --pipeline 'nbs->lib'
        nbl export --reverse
    """
    project = get_project(ctx)

    # Handle --reverse flag
    if reverse:
        if export_pipeline:
            console.print("[red]Error: Cannot use --reverse with --pipeline[/red]")
            raise typer.Exit(1)
        reversed_pipeline = project.get_reversed_pipeline()
        if not reversed_pipeline:
            console.print(
                "[yellow]No reversible pipeline rules found (module code locations are excluded)[/yellow]"
            )
            return
        export_pipeline = reversed_pipeline
        console.print(f"[blue]Using reversed pipeline: {export_pipeline}[/blue]")

    if dry_run:
        console.print("[blue]Dry run - would export:[/blue]")
        if export_pipeline:
            console.print(f"[blue]Using custom pipeline: {export_pipeline}[/blue]")
        nbs = project.get_notebooks()
        for nb in nbs:
            twins = project.get_notebook_twins(nb)
            console.print(f"  {nb.source_path}")
            for twin in twins:
                console.print(f"    -> {twin}")
        return

    if export_pipeline:
        console.print(f"[blue]Using custom pipeline: {export_pipeline}[/blue]")

    result = project.export(
        notebooks=notebooks,
        pipeline=export_pipeline,
        silence_warnings=silence_warnings,
    )

    # Print warnings (unless silenced)
    if result.warnings and not silence_warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")

    if result.success:
        console.print("[green]Export completed successfully[/green]")
        for f in result.files_created:
            console.print(f"  [green]+[/green] {f}")
    else:
        console.print("[red]Export completed with errors[/red]")
        for error in result.errors:
            console.print(f"  [red]Error:[/red] {error}")
        raise typer.Exit(1)

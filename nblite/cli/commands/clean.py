"""Clean command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command()
def clean(
    ctx: typer.Context,
    notebooks: Annotated[
        list[Path] | None,
        typer.Argument(help="Specific notebooks to clean"),
    ] = None,
    remove_outputs: Annotated[
        bool,
        typer.Option("-O", "--remove-outputs", help="Remove all outputs from code cells"),
    ] = False,
    remove_execution_counts: Annotated[
        bool,
        typer.Option(
            "-e", "--remove-execution-counts", help="Remove execution counts from code cells"
        ),
    ] = False,
    remove_cell_metadata: Annotated[
        bool,
        typer.Option("--remove-cell-metadata", help="Remove cell-level metadata"),
    ] = False,
    remove_notebook_metadata: Annotated[
        bool,
        typer.Option("--remove-notebook-metadata", help="Remove notebook-level metadata"),
    ] = False,
    remove_kernel_info: Annotated[
        bool,
        typer.Option("--remove-kernel-info", help="Remove kernel specification"),
    ] = False,
    preserve_cell_ids: Annotated[
        bool,
        typer.Option("--preserve-cell-ids/--remove-cell-ids", help="Preserve or remove cell IDs"),
    ] = True,
    remove_output_metadata: Annotated[
        bool,
        typer.Option("--remove-output-metadata", help="Remove metadata from outputs"),
    ] = False,
    remove_output_execution_counts: Annotated[
        bool,
        typer.Option(
            "--remove-output-execution-counts", help="Remove execution counts from output results"
        ),
    ] = False,
    keep_only: Annotated[
        str | None,
        typer.Option("--keep-only", help="Keep only these metadata keys (comma-separated)"),
    ] = None,
) -> None:
    """Clean notebooks by removing outputs and metadata.

    By default, uses sensible VCS defaults: removes execution counts, cell
    metadata, output metadata, and output execution counts. Outputs and
    kernel info are preserved. Options can be configured in nblite.toml
    under [clean].

    Examples:
        nbl clean                       # Clean with VCS defaults
        nbl clean -O                    # Also remove outputs
        nbl clean --remove-kernel-info  # Also remove kernel info
    """
    project = get_project(ctx)

    # Parse keep_only into list if provided
    keep_only_list = None
    if keep_only:
        keep_only_list = [k.strip() for k in keep_only.split(",")]

    # Pass CLI options as overrides (only if they differ from defaults)
    # For flags, we pass them if they're True (user explicitly set them)
    project.clean(
        notebooks=notebooks,
        remove_outputs=remove_outputs if remove_outputs else None,
        remove_execution_counts=remove_execution_counts if remove_execution_counts else None,
        remove_cell_metadata=remove_cell_metadata if remove_cell_metadata else None,
        remove_notebook_metadata=remove_notebook_metadata if remove_notebook_metadata else None,
        remove_kernel_info=remove_kernel_info if remove_kernel_info else None,
        preserve_cell_ids=preserve_cell_ids
        if not preserve_cell_ids
        else None,  # Only pass if False
        remove_output_metadata=remove_output_metadata if remove_output_metadata else None,
        remove_output_execution_counts=remove_output_execution_counts
        if remove_output_execution_counts
        else None,
        keep_only_metadata=keep_only_list,
    )
    console.print("[green]Notebooks cleaned[/green]")

"""
Clear command for nblite CLI.

Clears code locations downstream from a specified location.
"""

from __future__ import annotations

from typing import Annotated

import typer

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command()
def clear(
    ctx: typer.Context,
    code_location: Annotated[
        str | None,
        typer.Argument(
            help="The code location to clear (clears this location and all downstream locations).",
        ),
    ] = None,
    all_downstream: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Clear all downstream code locations (all non-top-level locations).",
        ),
    ] = False,
) -> None:
    """
    Clear code locations by removing generated files.

    Clears the specified code location and all locations downstream from it
    in the export pipeline. Top-level code locations (those not exported TO)
    cannot be cleared directly.

    Files like __init__.py and __main__.py in module folders are preserved.

    Examples:
        nbl clear pts       # Clear pts and all downstream (e.g., lib)
        nbl clear lib       # Clear only lib
        nbl clear --all     # Clear all non-top-level code locations
    """
    project = get_project(ctx)

    if not all_downstream and code_location is None:
        console.print("[red]Error: Either --all or a code location must be provided.[/red]")
        raise typer.Exit(1)

    if all_downstream and code_location is not None:
        console.print("[red]Error: Cannot specify both --all and a code location.[/red]")
        raise typer.Exit(1)

    # Get top-level code locations (those not exported to)
    top_level_locations = _get_top_level_code_locations(project)

    if all_downstream:
        # Clear all non-top-level code locations
        locations_to_clear = [
            key for key in project.code_locations.keys() if key not in top_level_locations
        ]
        if not locations_to_clear:
            console.print("[yellow]No downstream code locations to clear.[/yellow]")
            return
    else:
        # Validate the code location exists
        if code_location not in project.code_locations:
            available = ", ".join(project.code_locations.keys())
            console.print(
                f"[red]Error: Code location '{code_location}' not found. "
                f"Available locations: {available}[/red]"
            )
            raise typer.Exit(1)

        # Check if it's a top-level location
        if code_location in top_level_locations:
            console.print(
                f"[red]Error: '{code_location}' is a top-level code location and cannot be "
                f"cleared. Top-level locations are never exported to.[/red]"
            )
            raise typer.Exit(1)

        # Get this location and all downstream locations
        locations_to_clear = _get_location_and_downstream(project, code_location)

    # Clear the locations
    total_files_deleted = 0
    total_dirs_deleted = 0

    for loc_key in locations_to_clear:
        cl = project.code_locations[loc_key]
        files_deleted, dirs_deleted = _clear_code_location(cl)
        total_files_deleted += files_deleted
        total_dirs_deleted += dirs_deleted
        if files_deleted > 0 or dirs_deleted > 0:
            console.print(
                f"  Cleared [cyan]{loc_key}[/cyan]: {files_deleted} files, {dirs_deleted} directories"
            )

    if total_files_deleted == 0 and total_dirs_deleted == 0:
        console.print("[yellow]No files to clear.[/yellow]")
    else:
        console.print(
            f"[green]Cleared {total_files_deleted} files and {total_dirs_deleted} directories.[/green]"
        )


def _get_top_level_code_locations(project) -> set[str]:
    """
    Get all top-level code locations (those that are never exported TO).

    A top-level code location is one that appears only as a source (from_key)
    in the export pipeline, never as a destination (to_key).
    """

    # Collect all destination keys
    destination_keys: set[str] = set()
    for rule in project.config.export_pipeline:
        destination_keys.add(rule.to_key)

    # Top-level locations are those that are never destinations
    top_level: set[str] = set()
    for key in project.code_locations.keys():
        if key not in destination_keys:
            top_level.add(key)

    return top_level


def _get_location_and_downstream(project, start_key: str) -> list[str]:
    """
    Get the specified location and all locations downstream from it.

    Uses BFS to traverse the export pipeline graph.
    """
    visited: set[str] = set()
    to_visit = [start_key]
    result: list[str] = []

    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)
        result.append(current)

        # Find all rules where current is the source
        for rule in project.config.export_pipeline:
            if rule.from_key == current and rule.to_key not in visited:
                to_visit.append(rule.to_key)

    return result


def _clear_code_location(cl) -> tuple[int, int]:
    """
    Clear all files in a code location.

    For module format locations, preserves __init__.py and __main__.py files.

    Returns:
        Tuple of (files_deleted, directories_deleted)
    """
    from nblite.config.schema import CodeLocationFormat

    if not cl.path.exists():
        return 0, 0

    files_deleted = 0
    dirs_deleted = 0

    # Get the file extension for this format
    ext = cl.file_ext

    # Delete files matching the format
    for file_path in cl.path.glob(f"**/*{ext}"):
        if not file_path.is_file():
            continue

        # Handle .pct.py extension properly
        if ext == ".pct.py" and not file_path.name.endswith(".pct.py"):
            continue

        # For module format, skip __init__.py, __main__.py, and hidden files
        if cl.format == CodeLocationFormat.MODULE:
            if file_path.name.startswith("__") or file_path.name.startswith("."):
                continue

        file_path.unlink()
        files_deleted += 1

    # Remove empty directories (but not the root code location directory)
    # Walk from deepest directories first
    for dir_path in sorted(cl.path.glob("**/*"), key=lambda p: len(p.parts), reverse=True):
        if not dir_path.is_dir():
            continue
        if dir_path == cl.path:
            continue
        # Check if directory is empty
        if not any(dir_path.iterdir()):
            dir_path.rmdir()
            dirs_deleted += 1

    return files_deleted, dirs_deleted

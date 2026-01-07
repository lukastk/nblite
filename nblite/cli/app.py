"""
Main CLI application for nblite.

This module defines the `nbl` command and registers all subcommands.
"""

from __future__ import annotations

__all__ = ["app"]

import builtins
import json
from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import (
    ADD_CODE_LOCATION_KEY,
    CONFIG_OVERRIDE_KEY,
    CONFIG_PATH_KEY,
    console,
    version_callback,
)

# Create app first so commands can import and register themselves
app = typer.Typer(
    name="nbl",
    help="nblite - Notebook-driven Python package development tool",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to nblite.toml config file",
            envvar="NBLITE_CONFIG",
        ),
    ] = None,
    override_config: Annotated[
        str | None,
        typer.Option(
            "--override-config",
            help="JSON string to override config values (overwrites at key level)",
        ),
    ] = None,
    add_code_location: Annotated[
        builtins.list[str] | None,
        typer.Option(
            "--add-code-location",
            help='JSON string to add a code location: \'{"name": "cl_name", "path": "...", "format": "..."}\'',
        ),
    ] = None,
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
    ctx.ensure_object(dict)

    if config is not None:
        ctx.obj[CONFIG_PATH_KEY] = config

    # Parse and store override config
    if override_config is not None:
        try:
            ctx.obj[CONFIG_OVERRIDE_KEY] = json.loads(override_config)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in --override-config: {e}[/red]")
            raise typer.Exit(1) from None

    # Parse and store add code locations
    if add_code_location is not None:
        parsed_locations = []
        for loc_json in add_code_location:
            try:
                parsed = json.loads(loc_json)
                if "name" not in parsed:
                    console.print("[red]Error: --add-code-location requires 'name' field[/red]")
                    raise typer.Exit(1)
                parsed_locations.append(parsed)
            except json.JSONDecodeError as e:
                console.print(f"[red]Error: Invalid JSON in --add-code-location: {e}[/red]")
                raise typer.Exit(1) from None
        ctx.obj[ADD_CODE_LOCATION_KEY] = parsed_locations


from nblite.cli.commands import (  # noqa: E402, F401
    clean,
    clear,
    convert,
    docs,
    export,
    fill,
    from_module,
    hooks,
    info,
    init,
    list,
    nb_to_script,
    new,
    prepare,
    readme,
    templates,
)

if __name__ == "__main__":
    app()

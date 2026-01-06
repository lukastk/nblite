"""
Main CLI application for nblite.

This module defines the `nbl` command and registers all subcommands.
"""

from __future__ import annotations

__all__ = ["app"]

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import CONFIG_PATH_KEY, version_callback

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

"""
Main CLI application for nblite.

This module defines the `nbl` command and registers all subcommands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import CONFIG_PATH_KEY, version_callback

# Import command functions
from nblite.cli.commands.clean import clean
from nblite.cli.commands.convert import convert
from nblite.cli.commands.docs import preview_docs_cmd, render_docs_cmd
from nblite.cli.commands.export import export
from nblite.cli.commands.fill import fill, test
from nblite.cli.commands.from_module import from_module_cmd
from nblite.cli.commands.hooks import (
    hook_cmd,
    install_hooks_cmd,
    uninstall_hooks_cmd,
    validate_cmd,
)
from nblite.cli.commands.info import info
from nblite.cli.commands.init import init
from nblite.cli.commands.list import list_files
from nblite.cli.commands.new import new
from nblite.cli.commands.prepare import prepare
from nblite.cli.commands.readme import readme

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


# Register commands
app.command()(init)
app.command()(new)
app.command()(export)
app.command()(clean)
app.command()(convert)
app.command("from-module")(from_module_cmd)
app.command()(info)
app.command("list")(list_files)
app.command("install-hooks")(install_hooks_cmd)
app.command("uninstall-hooks")(uninstall_hooks_cmd)
app.command("validate")(validate_cmd)
app.command("hook")(hook_cmd)
app.command()(fill)
app.command()(test)
app.command()(readme)
app.command()(prepare)
app.command("render-docs")(render_docs_cmd)
app.command("preview-docs")(preview_docs_cmd)


if __name__ == "__main__":
    app()

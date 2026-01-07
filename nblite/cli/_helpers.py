"""Shared helpers for CLI commands."""

from __future__ import annotations

__all__ = [
    "console",
    "CONFIG_PATH_KEY",
    "CONFIG_OVERRIDE_KEY",
    "ADD_CODE_LOCATION_KEY",
    "version_callback",
    "get_project",
    "get_config_path",
]

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from nblite import __version__

if TYPE_CHECKING:
    from nblite.core.project import NbliteProject

console = Console()

# Global config keys stored in context
CONFIG_PATH_KEY = "config_path"
CONFIG_OVERRIDE_KEY = "config_override"
ADD_CODE_LOCATION_KEY = "add_code_location"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"nblite version {__version__}")
        raise typer.Exit()


def get_project(ctx: typer.Context) -> NbliteProject:
    """
    Get the NbliteProject using the config path from context.

    Args:
        ctx: Typer context containing optional config_path, config_override, add_code_location

    Returns:
        NbliteProject instance

    Raises:
        typer.Exit: If project cannot be loaded
    """
    from nblite.core.project import NbliteProject

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None
    config_override = ctx.obj.get(CONFIG_OVERRIDE_KEY) if ctx.obj else None
    add_code_locations = ctx.obj.get(ADD_CODE_LOCATION_KEY) if ctx.obj else None

    try:
        return NbliteProject.from_path(
            config_path,
            config_override=config_override,
            add_code_locations=add_code_locations,
        )
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


def get_config_path(ctx: typer.Context) -> Path | None:
    """Get the config path from context, if set."""
    return ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

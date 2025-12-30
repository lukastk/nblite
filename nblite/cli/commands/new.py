"""New command for nblite CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from nblite.cli._helpers import CONFIG_PATH_KEY, console


def new(
    ctx: typer.Context,
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

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    # Try to find project root
    try:
        project = NbliteProject.from_path(config_path)
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

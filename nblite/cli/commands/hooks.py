"""Git hooks commands for nblite CLI."""

from __future__ import annotations

from typing import Annotated

import typer

from nblite.cli._helpers import CONFIG_PATH_KEY, console, get_project
from nblite.cli.app import app


@app.command(name="install-hooks")
def install_hooks_cmd(ctx: typer.Context) -> None:
    """Install git hooks for the project."""
    from nblite.git.hooks import install_hooks

    project = get_project(ctx)

    try:
        install_hooks(project)
        console.print("[green]Git hooks installed[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@app.command(name="uninstall-hooks")
def uninstall_hooks_cmd(ctx: typer.Context) -> None:
    """Remove git hooks for the project."""
    from nblite.git.hooks import uninstall_hooks

    project = get_project(ctx)
    uninstall_hooks(project)
    console.print("[green]Git hooks removed[/green]")


@app.command(name="validate")
def validate_cmd(ctx: typer.Context) -> None:
    """Validate git staging state."""
    from nblite.git.staging import validate_staging

    project = get_project(ctx)

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


@app.command(name="hook")
def hook_cmd(
    ctx: typer.Context,
    hook_name: Annotated[
        str,
        typer.Argument(help="Hook name (pre-commit, post-commit)"),
    ],
) -> None:
    """Run a git hook (internal use)."""
    from nblite.core.project import NbliteProject

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    try:
        project = NbliteProject.from_path(config_path)
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

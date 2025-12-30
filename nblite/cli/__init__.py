"""
Command-line interface for nblite.

This module provides the `nbl` CLI command.
"""

import typer

app = typer.Typer(
    name="nbl",
    help="nblite - Notebook-driven Python package development tool",
    no_args_is_help=True,
)


def main() -> None:
    """Entry point for the nbl CLI."""
    app()


__all__ = ["app", "main"]

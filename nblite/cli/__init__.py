"""
Command-line interface for nblite.

This module provides the `nbl` CLI command.
"""

from nblite.cli.app import app


def main() -> None:
    """Entry point for the nbl CLI."""
    app()


__all__ = ["app", "main"]

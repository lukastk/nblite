"""
nblite - Notebook-driven Python package development tool.

A modern alternative to nbdev that enables developers to write Python packages
entirely in Jupyter notebooks, with automatic export to Python modules,
synchronization between formats, and integrated documentation generation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nblite.export.pipeline import ExportResult

try:
    from importlib.metadata import version

    __version__ = version("nblite")
except Exception:
    __version__ = "0.0.0.dev"  # Fallback for development without installation

# Environment variable to disable nbl_export
DISABLE_NBLITE_EXPORT_ENV_VAR = "NBLITE_DISABLE_EXPORT"


def nbl_export(
    root_path: str | Path | None = None,
    pipeline: str | None = None,
) -> ExportResult | None:
    """
    Export notebooks in an nblite project.

    This is a convenience function designed to be called from within notebooks
    to trigger export during development. Place this at the top of your notebook:

        from nblite import nbl_export; nbl_export()

    If root_path is not provided, nblite will search for a nblite.toml file
    in the current directory and all parent directories.

    Args:
        root_path: Path to the root folder of the nblite project.
                   If None, searches upward for nblite.toml.
        pipeline: Custom export pipeline string (e.g., 'nbs -> lib').
                  If None, uses the pipeline from config.

    Returns:
        ExportResult with success status and file lists, or None if export
        is disabled via environment variable.

    Example:
        >>> from nblite import nbl_export
        >>> nbl_export()  # Export using auto-detected project root
        >>> nbl_export(pipeline="nbs -> lib")  # Custom pipeline
    """
    # Check if export is disabled via environment variable
    disable_export = os.environ.get(DISABLE_NBLITE_EXPORT_ENV_VAR, "").lower()
    if disable_export in ("true", "1", "yes"):
        return None

    from nblite.config import find_config_file
    from nblite.core.project import NbliteProject

    # Find project root
    if root_path is None:
        config_file = find_config_file(Path.cwd())
        if config_file is None:
            raise FileNotFoundError(
                "Could not find nblite.toml in current directory or any parent directory. "
                "Please specify root_path or ensure you're in an nblite project."
            )
        root_path = config_file.parent
    else:
        root_path = Path(root_path)

    # Load project and run export
    project = NbliteProject.from_path(root_path)
    return project.export(pipeline=pipeline)


# Also export show_doc for convenience
from nblite.docs import show_doc  # noqa: E402

__all__ = [
    "__version__",
    "nbl_export",
    "show_doc",
    "DISABLE_NBLITE_EXPORT_ENV_VAR",
]

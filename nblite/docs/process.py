"""
Notebook processing for documentation generation.

This module handles converting notebooks to documentation-ready format:
- Injecting API documentation for exported cells
- Removing hidden cells
- Stripping directive lines
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nblite.core.notebook import Notebook
from nblite.docs.cell_docs import render_cell_doc

__all__ = ["process_notebook_for_docs"]


def process_notebook_for_docs(
    source_path: Path,
    dest_path: Path,
    source_format: str = "ipynb",
) -> None:
    """
    Process a notebook for documentation.

    This function:
    1. Converts the notebook to ipynb format if needed
    2. For cells with #|export directive, inserts API documentation
    3. Removes cells with #|hide or #|exporti directives
    4. Strips directive lines from remaining cells

    Args:
        source_path: Path to source notebook
        dest_path: Path to write processed notebook
        source_format: Format of source notebook (ipynb, percent)
    """
    # Load notebook
    nb = Notebook.from_file(source_path, format=source_format)

    # Process cells
    processed_cells: list[dict[str, Any]] = []

    for cell in nb.cells:
        cell_dict = cell.to_dict()

        if cell.is_code:
            # Check for directives that should hide the cell
            if cell.has_directive("hide") or cell.has_directive("exporti"):
                continue

            # For export cells, inject API documentation before the cell
            if cell.has_directive("export"):
                try:
                    doc_markdown = render_cell_doc(cell.source)
                    if doc_markdown.strip():
                        doc_cell = {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": doc_markdown,
                        }
                        processed_cells.append(doc_cell)
                except Exception:
                    # If documentation extraction fails, skip it
                    pass

            # Strip directive lines from cell source
            source_lines = cell.source.split("\n")
            clean_lines = []
            for line in source_lines:
                stripped = line.strip()
                # Keep Quarto directives (end with ':') but remove nblite directives
                if stripped.startswith("#|"):
                    directive_part = stripped[2:].split()[0] if stripped[2:].split() else ""
                    if directive_part.endswith(":"):
                        # Quarto directive, keep it
                        clean_lines.append(line)
                    # Otherwise skip the line (nblite directive)
                else:
                    clean_lines.append(line)

            cell_dict["source"] = "\n".join(clean_lines)

        processed_cells.append(cell_dict)

    # Create output notebook
    output_nb = {
        "cells": processed_cells,
        "metadata": nb.metadata,
        "nbformat": nb.nbformat,
        "nbformat_minor": nb.nbformat_minor,
    }

    # Write output
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "w") as f:
        json.dump(output_nb, f, indent=2)

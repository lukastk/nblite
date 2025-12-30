"""
Hash utilities for notebook change detection.

Calculates and stores source/output hashes in notebook metadata
to enable skipping unchanged notebooks during fill operations.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nblite.core.notebook import Notebook

__all__ = [
    "get_notebook_hash",
    "has_notebook_changed",
    "HASH_METADATA_KEY",
]

# Metadata key for storing the hash in notebooks
HASH_METADATA_KEY = "nblite_source_hash"


def _normalize_text_field(value: Any) -> Any:
    """Normalize text fields to always be strings for consistent hashing."""
    if isinstance(value, list):
        return "".join(value)
    return value


def _get_clean_output(output: dict[str, Any]) -> dict[str, Any]:
    """Get a cleaned output dict for hashing (excluding volatile fields)."""
    cleaned = {}
    for k, v in output.items():
        if k in ["metadata", "execution_count"]:
            continue
        # Normalize text fields (can be str or list depending on how it was read/written)
        if k == "text":
            v = _normalize_text_field(v)
        # Normalize data field values (e.g., text/plain can be str or list)
        elif k == "data" and isinstance(v, dict):
            v = {data_key: _normalize_text_field(data_val) for data_key, data_val in v.items()}
        cleaned[k] = v
    return cleaned


def _get_clean_cell(cell: dict[str, Any]) -> dict[str, Any]:
    """Get a cleaned cell dict for hashing."""
    source = cell.get("source", "")
    # Normalize source (can be str or list depending on how it was read/written)
    if isinstance(source, list):
        source = "".join(source)
    clean_cell: dict[str, Any] = {"source": source}
    if "outputs" in cell:
        clean_cell["outputs"] = [_get_clean_output(o) for o in cell["outputs"]]
    return clean_cell


def get_notebook_hash(notebook: Notebook) -> str:
    """
    Calculate a hash of the notebook's source code and outputs.

    The hash is calculated from:
    - Cell source code
    - Cell outputs (excluding volatile metadata like execution_count)

    Args:
        notebook: The notebook to hash.

    Returns:
        SHA256 hash string of the notebook content.
    """
    # Get the raw notebook dict
    nb_dict = notebook.to_dict()

    # Extract clean cells for hashing
    clean_cells = [_get_clean_cell(cell) for cell in nb_dict.get("cells", [])]

    # Calculate hash
    content = json.dumps(clean_cells, sort_keys=True)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def has_notebook_changed(notebook: Notebook) -> bool:
    """
    Check if a notebook has changed since its last fill.

    Compares the current hash with the stored hash in notebook metadata.

    Args:
        notebook: The notebook to check.

    Returns:
        True if the notebook has changed or has no stored hash.
    """
    # Get stored hash from metadata
    nb_dict = notebook.to_dict()
    metadata = nb_dict.get("metadata", {})
    stored_hash = metadata.get(HASH_METADATA_KEY)

    if stored_hash is None:
        return True

    # Calculate current hash
    current_hash = get_notebook_hash(notebook)

    return current_hash != stored_hash


def get_notebook_hash_from_path(path: Path | str) -> tuple[str, bool]:
    """
    Get the hash and change status for a notebook file.

    Args:
        path: Path to the notebook file.

    Returns:
        Tuple of (current_hash, has_changed).
    """
    from nblite.core.notebook import Notebook

    nb = Notebook.from_file(path)
    current_hash = get_notebook_hash(nb)
    has_changed = has_notebook_changed(nb)

    return current_hash, has_changed

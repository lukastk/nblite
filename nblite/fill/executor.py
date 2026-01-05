"""
Notebook execution for the fill feature.

Executes notebook cells and fills outputs, respecting skip directives.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from nblite.fill.hash import HASH_METADATA_KEY, get_notebook_hash

if TYPE_CHECKING:
    from nblite.core.notebook import Notebook

__all__ = [
    "fill_notebook",
    "FillResult",
    "FillStatus",
]


class FillStatus:
    """Status constants for fill operations."""

    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class FillResult:
    """Result of a fill operation."""

    status: str
    path: Path | None = None
    message: str = ""
    error: Exception | None = None


def _mark_skipped_cells(nb: nbformat.NotebookNode) -> tuple[nbformat.NotebookNode, list[int]]:
    """
    Mark cells that should be skipped during execution.

    Handles directives:
    - #|skip_evals: Start skipping cells
    - #|skip_evals_stop: Stop skipping cells
    - #|eval: false: Skip a single cell

    Args:
        nb: The notebook node.

    Returns:
        Tuple of (modified notebook, list of skipped cell indices).
    """
    skip_mode = False
    skipped_indices: list[int] = []

    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue

        skip_this_cell = False
        source = cell.get("source", "")

        for line in source.split("\n"):
            line = line.strip()
            if not line.startswith("#|"):
                continue

            directive = line[2:].strip()

            if directive == "skip_evals":
                if skip_mode:
                    raise ValueError(
                        f"Cell {idx}: Already in skip_evals mode. "
                        "Cannot nest #|skip_evals directives."
                    )
                skip_mode = True

            elif directive == "skip_evals_stop":
                if not skip_mode:
                    raise ValueError(
                        f"Cell {idx}: Not in skip_evals mode. "
                        "Cannot use #|skip_evals_stop without #|skip_evals."
                    )
                skip_mode = False

            elif directive.startswith("eval"):
                # Handle #|eval: false or #|eval:false
                parts = directive.split(":", 1)
                if len(parts) == 2:
                    value = parts[1].strip().lower()
                    if value == "false":
                        skip_this_cell = True

        # Mark cell for skipping
        if skip_mode or skip_this_cell:
            # Store original cell type and mark as skip
            cell["_original_cell_type"] = cell.cell_type
            cell.cell_type = "raw"  # Change to raw so it won't be executed
            skipped_indices.append(idx)

    return nb, skipped_indices


def _restore_skipped_cells(
    nb: nbformat.NotebookNode, skipped_indices: list[int]
) -> nbformat.NotebookNode:
    """Restore skipped cells to their original type."""
    for idx in skipped_indices:
        cell = nb.cells[idx]
        if "_original_cell_type" in cell:
            cell.cell_type = cell["_original_cell_type"]
            del cell["_original_cell_type"]
    return nb


def fill_notebook(
    notebook: Notebook | Path | str,
    *,
    timeout: int | None = None,
    working_dir: Path | str | None = None,
    dry_run: bool = False,
    remove_outputs_first: bool = False,
    clean: bool = True,
    save_hash: bool = True,
) -> FillResult:
    """
    Execute a notebook and fill its outputs.

    Args:
        notebook: The notebook to fill (Notebook object or path).
        timeout: Cell execution timeout in seconds (None = no timeout).
        working_dir: Working directory for execution (default: notebook's directory).
        dry_run: If True, execute but don't save the notebook.
        remove_outputs_first: If True, clear existing outputs before execution.
        clean: If True, clean the notebook after execution (removes execution
            metadata for cleaner VCS diffs). Cleaning happens before hash is
            computed to ensure hash validity.
        save_hash: If True, save the notebook hash in metadata for change detection.

    Returns:
        FillResult with status and any error information.
    """
    from nblite.core.notebook import Notebook

    # Handle path input
    if isinstance(notebook, (str, Path)):
        path = Path(notebook)
        notebook = Notebook.from_file(path)
    else:
        path = notebook.source_path

    if path is None:
        return FillResult(
            status=FillStatus.ERROR,
            message="Notebook has no source path",
        )

    # Set working directory
    if working_dir is None:
        working_dir = path.parent
    else:
        working_dir = Path(working_dir)

    try:
        # Read notebook with nbformat for execution
        with open(path, encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        # Optionally clear existing outputs
        if remove_outputs_first:
            for cell in nb.cells:
                if cell.cell_type == "code":
                    cell.outputs = []
                    cell.execution_count = None

        # Mark cells to skip
        nb, skipped_indices = _mark_skipped_cells(nb)

        # Execute the notebook
        ep = ExecutePreprocessor(
            timeout=timeout,
            kernel_name="python3",
        )
        resources = {"metadata": {"path": str(working_dir)}}

        ep.preprocess(nb, resources)

        # Restore skipped cells
        nb = _restore_skipped_cells(nb, skipped_indices)

        if not dry_run:
            # Convert to nblite Notebook for cleaning and hash calculation
            nb_obj = Notebook.from_dict(dict(nb))

            # Clean the notebook if requested (must happen BEFORE hash calculation)
            if clean:
                nb_obj = nb_obj.clean()

            # Calculate and store new hash if requested
            if save_hash:
                new_hash = get_notebook_hash(nb_obj)
                nb_obj.metadata[HASH_METADATA_KEY] = new_hash

            # Write back to file
            nb_obj.to_file(path)

        return FillResult(
            status=FillStatus.SUCCESS,
            path=path,
            message="Notebook executed successfully",
        )

    except Exception as e:
        return FillResult(
            status=FillStatus.ERROR,
            path=path,
            message=str(e),
            error=e,
        )


def fill_notebooks(
    notebooks: list[Path],
    *,
    timeout: int | None = None,
    dry_run: bool = False,
    remove_outputs_first: bool = False,
    clean: bool = True,
    save_hash: bool = True,
    skip_unchanged: bool = True,
    n_workers: int = 1,
    on_progress: callable | None = None,
) -> list[FillResult]:
    """
    Execute multiple notebooks and fill their outputs.

    Args:
        notebooks: List of notebook paths to fill.
        timeout: Cell execution timeout in seconds.
        dry_run: If True, execute but don't save notebooks.
        remove_outputs_first: If True, clear existing outputs before execution.
        clean: If True, clean notebooks after execution.
        save_hash: If True, save notebook hash in metadata.
        skip_unchanged: If True, skip notebooks that haven't changed.
        n_workers: Number of parallel workers (1 = sequential).
        on_progress: Optional callback(path, result) for progress updates.

    Returns:
        List of FillResult objects.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from nblite.fill.hash import has_notebook_changed

    results: list[FillResult] = []
    to_process: list[Path] = []

    # Filter unchanged notebooks if requested
    for path in notebooks:
        if skip_unchanged:
            from nblite.core.notebook import Notebook

            try:
                nb = Notebook.from_file(path)
                if not has_notebook_changed(nb):
                    result = FillResult(
                        status=FillStatus.SKIPPED,
                        path=path,
                        message="Skipped (unchanged)",
                    )
                    results.append(result)
                    if on_progress:
                        on_progress(path, result)
                    continue
            except Exception:
                pass  # If we can't check, process anyway

        to_process.append(path)

    # Process notebooks
    def process_one(path: Path) -> FillResult:
        result = fill_notebook(
            path,
            timeout=timeout,
            dry_run=dry_run,
            remove_outputs_first=remove_outputs_first,
            clean=clean,
            save_hash=save_hash,
        )
        if on_progress:
            on_progress(path, result)
        return result

    if n_workers <= 1:
        # Sequential execution
        for path in to_process:
            results.append(process_one(path))
    else:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(process_one, path): path for path in to_process}
            for future in as_completed(futures):
                results.append(future.result())

    return results

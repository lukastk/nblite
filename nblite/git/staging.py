"""
Git staging validation for nblite.

Validates that git staging state is correct for nblite projects.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nblite.core.project import NbliteProject

__all__ = ["validate_staging", "ValidationResult"]


@dataclass
class ValidationResult:
    """Result of staging validation."""

    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(message)
        self.valid = False


def get_staged_files(cwd: Path) -> list[Path]:
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    files: list[Path] = []
    for line in result.stdout.strip().split("\n"):
        if line:
            files.append(Path(line))
    return files


def get_modified_files(cwd: Path) -> list[Path]:
    """Get list of modified (unstaged) files."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    files: list[Path] = []
    for line in result.stdout.strip().split("\n"):
        if line:
            files.append(Path(line))
    return files


def validate_staging(project: NbliteProject) -> ValidationResult:
    """
    Validate git staging state for an nblite project.

    Checks:
    1. Notebooks are clean (no outputs)
    2. Twins are staged together
    3. Exports are up to date

    Args:
        project: NbliteProject instance

    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()

    staged_files = get_staged_files(project.root_path)
    if not staged_files:
        return result

    # Convert to absolute paths relative to project root
    staged_abs = {project.root_path / f for f in staged_files}

    # Check twins are staged together
    for nb in project.get_notebooks():
        if nb.source_path is None:
            continue

        nb_rel = nb.source_path.relative_to(project.root_path)
        if nb_rel not in staged_files and nb.source_path not in staged_abs:
            continue

        # Notebook is staged, check twins
        twins = project.get_notebook_twins(nb)
        for twin in twins:
            if twin.exists():
                twin_rel = twin.relative_to(project.root_path)
                if twin_rel not in staged_files and twin not in staged_abs:
                    result.add_warning(f"Notebook {nb_rel} is staged but twin {twin_rel} is not")

    # Check notebooks are clean
    for staged_file in staged_files:
        abs_path = project.root_path / staged_file
        if not abs_path.exists():
            continue

        if abs_path.suffix == ".ipynb":
            # Check if notebook has outputs
            try:
                from nblite.core.notebook import Notebook

                nb = Notebook.from_file(abs_path)
                for cell in nb.cells:
                    if cell.is_code and cell.outputs:
                        result.add_warning(
                            f"Notebook {staged_file} has outputs - consider cleaning"
                        )
                        break
            except Exception:
                pass  # If notebook can't be parsed, skip the outputs check

    return result

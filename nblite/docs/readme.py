"""
README generation from index notebook.

Generates README.md files from index notebooks in nblite projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nblite.core.notebook import Notebook
    from nblite.core.project import NbliteProject

__all__ = ["generate_readme"]


def generate_readme(
    project: NbliteProject,
    output_path: Path,
    *,
    index_notebook: str | None = None,
) -> None:
    """
    Generate README.md from an index notebook.

    Extracts markdown content from the index notebook and writes
    it to a README.md file. Code cells are formatted as code blocks.

    Args:
        project: The nblite project.
        output_path: Path to write README.md.
        index_notebook: Optional name of index notebook (default: auto-detect).

    Raises:
        FileNotFoundError: If no index notebook is found.

    Example:
        >>> from nblite.core.project import NbliteProject
        >>> project = NbliteProject.from_path()
        >>> generate_readme(project, project.root_path / "README.md")
    """
    # Find index notebook
    index_nb = _find_index_notebook(project, index_notebook)

    if index_nb is None:
        raise FileNotFoundError(
            "No index notebook found. Create an index.ipynb or "
            "specify the notebook name with index_notebook parameter."
        )

    # Generate markdown content
    content = _notebook_to_markdown(index_nb)

    # Write output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)


def _find_index_notebook(project: NbliteProject, notebook_name: str | None) -> Notebook | None:
    """Find the index notebook in the project."""

    notebooks = project.get_notebooks()

    if notebook_name:
        # Look for specific notebook
        for nb in notebooks:
            if nb.source_path and nb.source_path.stem == notebook_name:
                return nb
        return None

    # Look for common index notebook names
    index_names = {"index", "00_index", "00_intro", "readme", "00_readme"}

    for nb in notebooks:
        if nb.source_path and nb.source_path.stem.lower() in index_names:
            return nb

    return None


def _notebook_to_markdown(notebook: Notebook) -> str:
    """Convert notebook cells to markdown string."""
    lines: list[str] = []

    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            lines.append(cell.source)
            lines.append("")  # Empty line between cells
        elif cell.cell_type == "code":
            # Skip cells with certain directives
            if cell.has_directive("hide") or cell.has_directive("hide_input"):
                continue

            # Check for export directive - skip if export only
            if cell.has_directive("export") and not cell.has_directive("echo"):
                # Check if there's meaningful code to show
                source_clean = cell.source_without_directives.strip()
                if not source_clean:
                    continue

            source = cell.source_without_directives.strip()
            if source:
                lines.append("```python")
                lines.append(source)
                lines.append("```")
                lines.append("")

    return "\n".join(lines).strip() + "\n"

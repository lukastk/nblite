"""
README generation module for nblite.

Converts notebooks to markdown for README files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nblite.core.notebook import Notebook

__all__ = ["notebook_to_markdown", "generate_readme"]


def notebook_to_markdown(notebook: Notebook) -> str:
    """
    Convert a notebook to markdown format.

    Filters out cells with #|hide directive and converts
    code cells to fenced code blocks.

    Args:
        notebook: Notebook to convert

    Returns:
        Markdown string
    """
    sections: list[str] = []

    for cell in notebook.cells:
        # Skip cells with #|hide directive
        if cell.is_code and cell.has_directive("hide"):
            continue

        if cell.is_markdown:
            sections.append(cell.source)
        elif cell.is_code:
            # Get source without directive lines for cleaner output
            code = cell.source_without_directives.strip()
            if code:
                sections.append(f"```python\n{code}\n```")

            # Include outputs if present
            for output in cell.outputs:
                output_text = _format_output(output)
                if output_text:
                    sections.append(output_text)

    return "\n\n".join(sections)


def _format_output(output: dict) -> str | None:
    """
    Format a cell output for markdown.

    Args:
        output: Output dictionary

    Returns:
        Formatted output string, or None if output should be skipped
    """
    output_type = output.get("output_type")

    if output_type == "stream":
        text = output.get("text", "")
        if isinstance(text, list):
            text = "".join(text)
        if text.strip():
            return f"```\n{text.strip()}\n```"

    elif output_type in ("execute_result", "display_data"):
        data = output.get("data", {})

        # Prefer text/plain for README
        if "text/plain" in data:
            text = data["text/plain"]
            if isinstance(text, list):
                text = "".join(text)
            if text.strip():
                return f"```\n{text.strip()}\n```"

        # Could also handle images/HTML but skip for now

    elif output_type == "error":
        # Skip errors in README
        pass

    return None


def generate_readme(
    notebook_path: Path,
    output_path: Path | None = None,
) -> str:
    """
    Generate README.md from a notebook.

    Args:
        notebook_path: Path to source notebook
        output_path: Path to write README.md (None = don't write)

    Returns:
        Generated markdown content
    """
    from nblite.core.notebook import Notebook

    notebook = Notebook.from_file(notebook_path)
    markdown = notebook_to_markdown(notebook)

    if output_path:
        output_path.write_text(markdown)

    return markdown

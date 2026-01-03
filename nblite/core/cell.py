"""
Cell class for nblite.

Wraps notebook cells with directive parsing support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from nblite.core.directive import (
    Directive,
    get_source_without_directives,
    parse_directives_from_source,
)

if TYPE_CHECKING:
    from nblite.core.notebook import Notebook

__all__ = ["Cell", "CellType"]


class CellType:
    """Cell type constants."""

    CODE = "code"
    MARKDOWN = "markdown"
    RAW = "raw"


@dataclass
class Cell:
    """
    Wrapper around a notebook cell with directive parsing.

    Attributes:
        cell_type: Type of cell (code, markdown, raw)
        source: Cell source content
        metadata: Cell metadata dictionary
        outputs: Cell outputs (for code cells)
        execution_count: Execution count (for code cells)
        id: Cell ID (nbformat 4.5+)
        index: Cell index in the notebook
        notebook: Reference to the parent notebook (optional)

    Example:
        >>> # Access cells from a notebook
        >>> nb = Notebook.from_file("example.ipynb")
        >>> for cell in nb.cells:
        ...     if cell.is_code and cell.has_directive("export"):
        ...         print(cell.source_without_directives)
    """

    cell_type: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    execution_count: int | None = None
    id: str | None = None
    index: int = 0
    notebook: Notebook | None = field(default=None, repr=False)

    _directives: dict[str, list[Directive]] | None = field(default=None, repr=False, init=False)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        index: int = 0,
        notebook: Notebook | None = None,
    ) -> Cell:
        """
        Create a Cell from a notebook cell dictionary.

        Args:
            data: Cell dictionary from notebook JSON
            index: Cell index in notebook
            notebook: Parent notebook reference

        Returns:
            Cell instance
        """
        # Handle source as list or string
        source = data.get("source", "")
        if isinstance(source, list):
            source = "".join(source)

        return cls(
            cell_type=data.get("cell_type", CellType.CODE),
            source=source,
            metadata=data.get("metadata", {}),
            outputs=data.get("outputs", []),
            execution_count=data.get("execution_count"),
            id=data.get("id"),
            index=index,
            notebook=notebook,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert cell to dictionary for notebook JSON.

        Returns:
            Cell dictionary
        """
        result: dict[str, Any] = {
            "cell_type": self.cell_type,
            "source": self.source,
            "metadata": self.metadata,
        }

        # Include cell ID if present (nbformat 4.5+)
        if self.id is not None:
            result["id"] = self.id

        if self.cell_type == CellType.CODE:
            result["outputs"] = self.outputs
            result["execution_count"] = self.execution_count

        return result

    @property
    def directives(self) -> dict[str, list[Directive]]:
        """
        All directives in this cell, indexed by directive name.

        Returns:
            Dictionary mapping directive names to lists of Directive objects
        """
        if self._directives is None:
            self._parse_directives()
        return self._directives  # type: ignore

    def _parse_directives(self) -> None:
        """Parse directives from cell source."""
        self._directives = {}
        if self.cell_type != CellType.CODE:
            return

        parsed = parse_directives_from_source(self.source, validate=False, cell=self)
        for directive in parsed:
            if directive.name not in self._directives:
                self._directives[directive.name] = []
            self._directives[directive.name].append(directive)

    @property
    def source_without_directives(self) -> str:
        """
        Cell source with directive lines removed.

        Returns:
            Source code without directive lines
        """
        if self.cell_type != CellType.CODE:
            return self.source
        return get_source_without_directives(self.source)

    @property
    def is_code(self) -> bool:
        """Check if this is a code cell."""
        return self.cell_type == CellType.CODE

    @property
    def is_markdown(self) -> bool:
        """Check if this is a markdown cell."""
        return self.cell_type == CellType.MARKDOWN

    @property
    def is_raw(self) -> bool:
        """Check if this is a raw cell."""
        return self.cell_type == CellType.RAW

    def has_directive(self, name: str) -> bool:
        """
        Check if cell has a specific directive.

        Args:
            name: Directive name to check for

        Returns:
            True if directive exists in cell
        """
        return name in self.directives

    def get_directive(self, name: str) -> Directive | None:
        """
        Get first directive with given name, or None.

        Args:
            name: Directive name

        Returns:
            First Directive with that name, or None
        """
        directives = self.directives.get(name, [])
        return directives[0] if directives else None

    def get_directives(self, name: str) -> list[Directive]:
        """
        Get all directives with given name.

        Args:
            name: Directive name

        Returns:
            List of Directive objects (empty if none found)
        """
        return self.directives.get(name, [])

    def __repr__(self) -> str:
        source_preview = self.source[:50] + "..." if len(self.source) > 50 else self.source
        source_preview = source_preview.replace("\n", "\\n")
        return f"Cell(type={self.cell_type!r}, index={self.index}, source={source_preview!r})"

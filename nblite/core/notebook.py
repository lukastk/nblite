"""
Notebook class for nblite.

Extends notebookx notebook functionality with directive parsing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import notebookx

from nblite.core.cell import Cell
from nblite.core.directive import Directive

__all__ = ["Notebook", "Format", "FormatError"]


class FormatError(ValueError):
    """Error raised when format cannot be determined or is invalid."""

    pass


class Format(Enum):
    """Notebook format constants."""

    IPYNB = "ipynb"
    PERCENT = "percent"

    @classmethod
    def get_valid_formats(self) -> list[str]:
        """All valid format strings."""
        return [f.value for f in self]

    @classmethod
    def validate(cls, fmt: str | Format) -> str:
        """Validate that a format string is valid.

        Args:
            fmt: Format string or Format enum member to validate

        Returns:
            The validated format string

        Raises:
            FormatError: If format is not valid
        """
        # Handle enum members
        if isinstance(fmt, cls):
            return fmt.value
        if fmt not in cls.get_valid_formats():
            raise FormatError(
                f"Invalid format '{fmt}'. Valid formats are: {cls.get_valid_formats()}"
            )
        return fmt

    @classmethod
    def from_extension(cls, ext: str) -> Format:
        """Get format from file extension.

        Delegates to notebookx.format_from_extension().

        Raises:
            FormatError: If format cannot be inferred from extension
        """
        nbx_fmt = notebookx.format_from_extension(ext)
        if nbx_fmt is not None:
            return cls.from_notebookx(nbx_fmt)
        raise FormatError(f"Cannot infer format from extension '{ext}'")

    @classmethod
    def from_path(cls, path: Path) -> Format:
        """Infer format from file path.

        Delegates to notebookx.format_from_path().

        Raises:
            FormatError: If format cannot be inferred from path
        """
        nbx_fmt = notebookx.format_from_path(str(path))
        if nbx_fmt is not None:
            return cls.from_notebookx(nbx_fmt)
        raise FormatError(f"Cannot infer format from path '{path}'")

    @classmethod
    def to_notebookx(cls, fmt: str | Format) -> notebookx.Format:
        """Convert string format or Format enum to notebookx Format enum.

        Raises:
            FormatError: If format is not valid
        """
        fmt_str = cls.validate(fmt)
        if fmt_str == cls.PERCENT.value:
            return notebookx.Format.Percent
        elif fmt_str == cls.IPYNB.value:
            return notebookx.Format.Ipynb
        else:
            raise FormatError(f"Invalid format '{fmt}'")

    @classmethod
    def from_notebookx(cls, fmt: notebookx.Format) -> Format:
        """Convert notebookx Format enum to Format enum."""
        if fmt == notebookx.Format.Percent:
            return cls.PERCENT
        elif fmt == notebookx.Format.Ipynb:
            return cls.IPYNB
        else:
            raise FormatError(f"Invalid notebookx format '{fmt}'")


@dataclass
class Notebook:
    """
    Extended Notebook class with directive parsing and nblite metadata.

    This class wraps notebookx functionality and provides:
    - Cell access with directive parsing
    - Directive aggregation across cells
    - Format conversion utilities

    Attributes:
        cells: List of Cell objects
        metadata: Notebook-level metadata
        nbformat: Notebook format version
        nbformat_minor: Notebook format minor version
        source_path: Original file path (if loaded from file)
        code_location: Code location key this notebook belongs to

    Example:
        >>> # Load a notebook from file
        >>> nb = Notebook.from_file("nbs/core.ipynb")
        >>> print(f"Notebook has {len(nb.cells)} cells")
        >>>
        >>> # Access directives
        >>> if nb.has_directive("default_exp"):
        ...     module = nb.get_directive("default_exp").value
        >>>
        >>> # Convert to different format
        >>> percent_str = nb.to_string("percent")
        >>> nb.to_file("output.pct.py", format="percent")
    """

    cells: list[Cell] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    nbformat: int = 4
    nbformat_minor: int = 5
    source_path: Path | None = None
    code_location: str | None = None

    _directives: dict[str, list[Directive]] | None = field(default=None, repr=False, init=False)

    @classmethod
    def from_file(
        cls,
        path: Path | str,
        format: str | None = None,
    ) -> Notebook:
        """
        Load notebook from file with directive parsing.

        Args:
            path: Path to notebook file
            format: Format hint (ipynb, percent). Auto-detected if None.

        Returns:
            Notebook instance
        """
        path = Path(path)

        if format is None:
            format = Format.from_path(path)

        # Use notebookx to load and convert to ipynb JSON
        nbx_format = Format.to_notebookx(format)
        nbx_nb = notebookx.Notebook.from_file(str(path), nbx_format)

        # Get the ipynb JSON representation
        ipynb_str = nbx_nb.to_string(notebookx.Format.Ipynb)
        data = json.loads(ipynb_str)

        return cls.from_dict(data, source_path=path)

    @classmethod
    def from_string(
        cls,
        content: str,
        format: str = Format.IPYNB,
        source_path: Path | None = None,
    ) -> Notebook:
        """
        Load notebook from string content.

        Args:
            content: Notebook content as string
            format: Format of the content (ipynb, percent)
            source_path: Optional source path to record

        Returns:
            Notebook instance
        """
        nbx_format = Format.to_notebookx(format)
        nbx_nb = notebookx.Notebook.from_string(content, nbx_format)

        # Get the ipynb JSON representation
        ipynb_str = nbx_nb.to_string(notebookx.Format.Ipynb)
        data = json.loads(ipynb_str)

        return cls.from_dict(data, source_path=source_path)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        source_path: Path | None = None,
    ) -> Notebook:
        """
        Create Notebook from dictionary (ipynb JSON structure).

        Args:
            data: Notebook dictionary
            source_path: Optional source path to record

        Returns:
            Notebook instance
        """
        notebook = cls(
            metadata=data.get("metadata", {}),
            nbformat=data.get("nbformat", 4),
            nbformat_minor=data.get("nbformat_minor", 5),
            source_path=source_path,
        )

        # Parse cells
        cells_data = data.get("cells", [])
        for i, cell_data in enumerate(cells_data):
            cell = Cell.from_dict(cell_data, index=i, notebook=notebook)
            notebook.cells.append(cell)

        return notebook

    @classmethod
    def from_notebookx(
        cls,
        nb: notebookx.Notebook,
        source_path: Path | None = None,
    ) -> Notebook:
        """
        Create from a notebookx Notebook instance.

        Args:
            nb: notebookx Notebook object
            source_path: Optional source path to record

        Returns:
            Notebook instance
        """
        ipynb_str = nb.to_string(notebookx.Format.Ipynb)
        data = json.loads(ipynb_str)
        return cls.from_dict(data, source_path=source_path)

    def to_notebookx(self) -> notebookx.Notebook:
        """
        Convert to a notebookx Notebook instance.

        Returns:
            notebookx Notebook object
        """
        ipynb_str = json.dumps(self.to_dict())
        return notebookx.Notebook.from_string(ipynb_str, notebookx.Format.Ipynb)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (ipynb JSON structure).

        Returns:
            Notebook dictionary
        """
        return {
            "cells": [cell.to_dict() for cell in self.cells],
            "metadata": self.metadata,
            "nbformat": self.nbformat,
            "nbformat_minor": self.nbformat_minor,
        }

    def to_string(self, format: str = Format.IPYNB) -> str:
        """
        Convert notebook to string in specified format.

        Args:
            format: Output format (ipynb, percent)

        Returns:
            Notebook content as string
        """
        # Convert to ipynb JSON first
        ipynb_str = json.dumps(self.to_dict(), indent=2)

        if format == Format.IPYNB:
            return ipynb_str

        # Use notebookx for format conversion
        nbx_nb = notebookx.Notebook.from_string(ipynb_str, notebookx.Format.Ipynb)
        nbx_format = Format.to_notebookx(format)
        return nbx_nb.to_string(nbx_format)

    def to_file(self, path: Path | str, format: str | None = None) -> None:
        """
        Save notebook to file.

        Args:
            path: Output file path
            format: Output format. Auto-detected from path if None.
        """
        path = Path(path)

        if format is None:
            format = Format.from_path(path)

        content = self.to_string(format)
        path.write_text(content)

    def clean(
        self,
        *,
        remove_outputs: bool = False,
        remove_execution_counts: bool = True,
        remove_cell_metadata: bool = True,
        remove_notebook_metadata: bool = False,
        remove_kernel_info: bool = False,
        preserve_cell_ids: bool = True,
        remove_output_metadata: bool = True,
        remove_output_execution_counts: bool = True,
        keep_only_metadata: list[str] | None = None,
    ) -> Notebook:
        """
        Return a cleaned copy of this notebook.

        Defaults are based on notebookx.CleanOptions.for_vcs() which provides
        sensible defaults for version control. Note: preserve_cell_ids defaults
        to True (unlike for_vcs) for idempotency.
        This delegates to notebookx for the actual cleaning.

        Args:
            remove_outputs: Remove all outputs from code cells
            remove_execution_counts: Remove execution counts from code cells
            remove_cell_metadata: Remove cell-level metadata
            remove_notebook_metadata: Remove notebook-level metadata
            remove_kernel_info: Remove kernel specification
            preserve_cell_ids: Preserve cell IDs (if False, cell IDs are removed)
            remove_output_metadata: Remove metadata from outputs
            remove_output_execution_counts: Remove execution counts from output results
            keep_only_metadata: Keep only these metadata keys (None = keep all)

        Returns:
            New Notebook instance with cleaned content
        """
        # Convert to notebookx Notebook
        nbx_nb = self.to_notebookx()

        # Create CleanOptions for notebookx
        # Map keep_only_metadata to allowed_*_metadata_keys
        allowed_cell_keys = keep_only_metadata if keep_only_metadata else None
        allowed_nb_keys = keep_only_metadata if keep_only_metadata else None

        clean_options = notebookx.CleanOptions(
            remove_outputs=remove_outputs,
            remove_execution_counts=remove_execution_counts,
            remove_cell_metadata=remove_cell_metadata,
            remove_notebook_metadata=remove_notebook_metadata,
            remove_kernel_info=remove_kernel_info,
            preserve_cell_ids=preserve_cell_ids,
            remove_output_metadata=remove_output_metadata,
            remove_output_execution_counts=remove_output_execution_counts,
            allowed_cell_metadata_keys=allowed_cell_keys,
            allowed_notebook_metadata_keys=allowed_nb_keys,
        )

        # Clean using notebookx
        cleaned_nbx = nbx_nb.clean(clean_options)

        # Convert back to nblite Notebook
        return Notebook.from_notebookx(cleaned_nbx, source_path=self.source_path)

    @property
    def directives(self) -> dict[str, list[Directive]]:
        """
        All directives in the notebook, indexed by directive name.

        Returns:
            Dictionary mapping directive names to lists of Directive objects
        """
        if self._directives is None:
            self._aggregate_directives()
        return self._directives  # type: ignore

    def _aggregate_directives(self) -> None:
        """Aggregate directives from all cells."""
        self._directives = {}
        for cell in self.cells:
            for name, cell_directives in cell.directives.items():
                if name not in self._directives:
                    self._directives[name] = []
                self._directives[name].extend(cell_directives)

    def get_directive(self, name: str) -> Directive | None:
        """
        Get the first (or only) directive with the given name.

        Args:
            name: Directive name

        Returns:
            First Directive with that name, or None
        """
        directives = self.directives.get(name, [])
        return directives[0] if directives else None

    def get_directives(self, name: str) -> list[Directive]:
        """
        Get all directives with the given name.

        Args:
            name: Directive name

        Returns:
            List of Directive objects (empty if none found)
        """
        return self.directives.get(name, [])

    @property
    def default_exp(self) -> str | None:
        """
        The default export module name from #|default_exp directive.

        Returns:
            Module path string, or None if not set
        """
        directive = self.get_directive("default_exp")
        if directive:
            return directive.value_parsed
        return None

    @property
    def exported_cells(self) -> list[Cell]:
        """
        Cells marked for export with #|export directive.

        Returns:
            List of cells with export directive
        """
        return [cell for cell in self.cells if cell.has_directive("export")]

    @property
    def code_cells(self) -> list[Cell]:
        """All code cells in the notebook."""
        return [cell for cell in self.cells if cell.is_code]

    @property
    def markdown_cells(self) -> list[Cell]:
        """All markdown cells in the notebook."""
        return [cell for cell in self.cells if cell.is_markdown]

    def __len__(self) -> int:
        """Return number of cells."""
        return len(self.cells)

    def __iter__(self):
        """Iterate over cells."""
        return iter(self.cells)

    def __getitem__(self, index: int) -> Cell:
        """Get cell by index."""
        return self.cells[index]

    def __repr__(self) -> str:
        path_str = str(self.source_path) if self.source_path else "None"
        return f"Notebook(path={path_str!r}, cells={len(self.cells)})"

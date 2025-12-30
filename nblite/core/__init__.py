"""
Core data models for nblite.

This module contains the core classes:
- Notebook: Extended notebook with directive support
- Cell: Cell wrapper with directive parsing
- Directive: Represents parsed directives
- CodeLocation: Represents a code location in the project
- PyFile: Represents a Python module file
- NbliteProject: Central project management class
"""

from nblite.core.cell import Cell, CellType
from nblite.core.code_location import CodeLocation
from nblite.core.directive import (
    Directive,
    DirectiveDefinition,
    DirectiveError,
    get_directive_definition,
    get_source_without_directives,
    list_directive_definitions,
    parse_directives_from_source,
    register_directive,
)
from nblite.core.notebook import Format, Notebook
from nblite.core.project import NbliteProject, NotebookLineage
from nblite.core.pyfile import PyFile, PyFileCell

__all__ = [
    # Cell
    "Cell",
    "CellType",
    # Notebook
    "Notebook",
    "Format",
    # CodeLocation
    "CodeLocation",
    # PyFile
    "PyFile",
    "PyFileCell",
    # Project
    "NbliteProject",
    "NotebookLineage",
    # Directive
    "Directive",
    "DirectiveDefinition",
    "DirectiveError",
    "register_directive",
    "get_directive_definition",
    "list_directive_definitions",
    "parse_directives_from_source",
    "get_source_without_directives",
]

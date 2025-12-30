"""
Documentation generation for nblite.

This module handles:
- Documentation generator protocol
- Multiple documentation generators (MkDocs, JupyterBook, Quarto)
- API documentation extraction from code cells
- README generation from notebooks
"""

from nblite.docs.cell_docs import (
    extract_class_meta,
    extract_class_meta_from_obj,
    extract_function_meta,
    extract_function_meta_from_obj,
    extract_top_level_definitions,
    render_cell_doc,
    render_class_doc,
    render_function_doc,
    show_doc,
)
from nblite.docs.generator import DocsGenerator, get_generator
from nblite.docs.jupyterbook import JupyterBookGenerator
from nblite.docs.mkdocs import MkDocsGenerator
from nblite.docs.process import process_notebook_for_docs
from nblite.docs.quarto import QuartoGenerator
from nblite.docs.readme import generate_readme

__all__ = [
    # Generators
    "DocsGenerator",
    "get_generator",
    "JupyterBookGenerator",
    "MkDocsGenerator",
    "QuartoGenerator",
    # Cell documentation
    "extract_top_level_definitions",
    "extract_function_meta",
    "extract_function_meta_from_obj",
    "extract_class_meta",
    "extract_class_meta_from_obj",
    "render_function_doc",
    "render_class_doc",
    "render_cell_doc",
    "show_doc",
    # Processing
    "process_notebook_for_docs",
    # README
    "generate_readme",
]

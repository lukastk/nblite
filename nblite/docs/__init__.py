"""
Documentation generation for nblite.

This module handles:
- Documentation generator protocol
- Jupyter Book generator
- MkDocs generator
"""

from nblite.docs.generator import DocsGenerator, get_generator
from nblite.docs.jupyterbook import JupyterBookGenerator
from nblite.docs.mkdocs import MkDocsGenerator
from nblite.docs.readme import generate_readme

__all__ = [
    "DocsGenerator",
    "get_generator",
    "JupyterBookGenerator",
    "MkDocsGenerator",
    "generate_readme",
]

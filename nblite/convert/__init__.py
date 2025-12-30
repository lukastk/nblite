"""
Conversion utilities for nblite.

This module provides functions for converting between different formats:
- module_to_notebook: Convert Python modules to notebooks
"""

from nblite.convert.from_module import module_to_notebook, modules_to_notebooks

__all__ = ["module_to_notebook", "modules_to_notebooks"]

"""
Extension system for nblite.

This module handles:
- Hook types and registry
- Extension loading
"""

from nblite.extensions.hooks import HookRegistry, HookType, hook
from nblite.extensions.loader import load_extension, load_extensions

__all__ = [
    "HookType",
    "HookRegistry",
    "hook",
    "load_extension",
    "load_extensions",
]

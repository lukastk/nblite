"""
Git integration for nblite.

This module handles:
- Git hook installation and management
- Staging validation
"""

from nblite.git.hooks import find_git_root, install_hooks, uninstall_hooks
from nblite.git.staging import ValidationResult, validate_staging

__all__ = [
    "install_hooks",
    "uninstall_hooks",
    "find_git_root",
    "validate_staging",
    "ValidationResult",
]

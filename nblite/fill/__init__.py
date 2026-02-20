"""
Fill module for nblite.

Provides functionality to execute notebooks and fill their outputs.
"""

from nblite.fill.executor import (
    FillResult,
    FillStatus,
    fill_notebook,
    fill_notebooks,
)
from nblite.fill.hash import (
    HASH_METADATA_KEY,
    get_notebook_hash,
    get_notebook_hash_from_path,
    has_notebook_changed,
)
from nblite.fill.kernel import (
    CUSTOM_KERNEL_NAME,
    custom_kernel_environment,
    validate_python_binary,
)

__all__ = [
    "fill_notebook",
    "fill_notebooks",
    "FillResult",
    "FillStatus",
    "get_notebook_hash",
    "get_notebook_hash_from_path",
    "has_notebook_changed",
    "HASH_METADATA_KEY",
    "validate_python_binary",
    "custom_kernel_environment",
    "CUSTOM_KERNEL_NAME",
]

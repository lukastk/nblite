"""
Extension loading for nblite.

Handles loading extensions from file paths and Python module paths.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

__all__ = ["load_extension", "load_extensions"]


def load_extension(
    *,
    path: str | Path | None = None,
    module: str | None = None,
) -> Any:
    """
    Load an extension from a file path or Python module.

    Extensions are Python files that can register hooks and add functionality
    to nblite. They are executed when loaded, allowing decorators like @hook
    to register callbacks.

    Args:
        path: Path to a Python file to load as an extension.
        module: Python import path (e.g., "mypackage.extension").

    Returns:
        The loaded module object.

    Raises:
        ValueError: If neither path nor module is specified, or both are.
        FileNotFoundError: If the path doesn't exist.
        ImportError: If the module can't be imported.

    Example:
        >>> # Load from file
        >>> load_extension(path="./my_extension.py")
        >>>
        >>> # Load from installed package
        >>> load_extension(module="mypackage.nblite_hooks")
    """
    if path is None and module is None:
        raise ValueError("Either path or module must be specified")
    if path is not None and module is not None:
        raise ValueError("Only one of path or module can be specified")

    if path is not None:
        return _load_from_path(Path(path))
    else:
        assert module is not None
        return _load_from_module(module)


def load_extensions(extensions: list[dict[str, str]]) -> list[Any]:
    """
    Load multiple extensions from a list of specifications.

    Args:
        extensions: List of dicts with either 'path' or 'module' key.

    Returns:
        List of loaded module objects.

    Example:
        >>> load_extensions([
        ...     {"path": "./ext1.py"},
        ...     {"module": "mypackage.ext2"},
        ... ])
    """
    modules = []
    for ext in extensions:
        path = ext.get("path")
        module = ext.get("module")
        loaded = load_extension(path=path, module=module)
        modules.append(loaded)
    return modules


def _load_from_path(path: Path) -> Any:
    """Load an extension from a file path."""
    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"Extension file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Extension path is not a file: {path}")

    # Create a unique module name based on the path
    module_name = f"nblite_ext_{path.stem}_{id(path)}"

    # Load the module using importlib
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load extension from: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    # Execute the module (this registers hooks via decorators)
    spec.loader.exec_module(module)

    return module


def _load_from_module(module_path: str) -> Any:
    """Load an extension from a Python import path."""
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import extension module: {module_path}") from e

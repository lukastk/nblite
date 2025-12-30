"""
Hook system for nblite extensions.

Provides a simple hook/callback mechanism for extending nblite behavior.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from typing import Any

__all__ = ["HookType", "HookRegistry", "hook"]


class HookType(Enum):
    """Types of hooks that can be registered."""

    # Export hooks
    PRE_EXPORT = "pre_export"
    POST_EXPORT = "post_export"

    # Notebook-level export hooks
    PRE_NOTEBOOK_EXPORT = "pre_notebook_export"
    POST_NOTEBOOK_EXPORT = "post_notebook_export"

    # Cell-level export hooks
    PRE_CELL_EXPORT = "pre_cell_export"
    POST_CELL_EXPORT = "post_cell_export"

    # Clean hooks
    PRE_CLEAN = "pre_clean"
    POST_CLEAN = "post_clean"

    # Directive hooks
    DIRECTIVE_PARSED = "directive_parsed"


# Type alias for hook callbacks
HookCallback = Callable[..., Any]


class HookRegistry:
    """
    Registry for hook callbacks.

    A global registry that manages all registered hooks. Extensions can
    register callbacks that will be invoked at specific points in the
    nblite workflow.

    Example:
        >>> from nblite.extensions import HookRegistry, HookType
        >>>
        >>> def my_callback(**kwargs):
        ...     print(f"Export starting for: {kwargs.get('project')}")
        >>>
        >>> HookRegistry.register(HookType.PRE_EXPORT, my_callback)
    """

    _hooks: dict[HookType, list[HookCallback]] = defaultdict(list)

    @classmethod
    def register(cls, hook_type: HookType, callback: HookCallback) -> None:
        """
        Register a callback for a hook type.

        Args:
            hook_type: The type of hook to register for.
            callback: The callback function to invoke.
        """
        cls._hooks[hook_type].append(callback)

    @classmethod
    def trigger(cls, hook_type: HookType, **context: Any) -> list[Any]:
        """
        Trigger all callbacks for a hook type.

        Args:
            hook_type: The type of hook to trigger.
            **context: Context arguments passed to all callbacks.

        Returns:
            List of return values from all callbacks.
        """
        results = []
        for callback in cls._hooks.get(hook_type, []):
            result = callback(**context)
            results.append(result)
        return results

    @classmethod
    def clear(cls, hook_type: HookType | None = None) -> None:
        """
        Clear registered hooks.

        Args:
            hook_type: Specific hook type to clear, or None to clear all.
        """
        if hook_type is None:
            cls._hooks.clear()
        else:
            cls._hooks[hook_type] = []

    @classmethod
    def get_hooks(cls, hook_type: HookType) -> list[HookCallback]:
        """
        Get all registered callbacks for a hook type.

        Args:
            hook_type: The type of hook to get callbacks for.

        Returns:
            List of registered callbacks.
        """
        return list(cls._hooks.get(hook_type, []))


def hook(hook_type: HookType) -> Callable[[HookCallback], HookCallback]:
    """
    Decorator to register a function as a hook callback.

    Example:
        >>> from nblite.extensions import hook, HookType
        >>>
        >>> @hook(HookType.PRE_EXPORT)
        ... def before_export(**kwargs):
        ...     print("About to export...")

    Args:
        hook_type: The type of hook to register for.

    Returns:
        Decorator function.
    """

    def decorator(func: HookCallback) -> HookCallback:
        HookRegistry.register(hook_type, func)
        return func

    return decorator

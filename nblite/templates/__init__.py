"""
Template handling for nblite.

This module handles notebook templates and Jinja2 rendering.
"""

from pathlib import Path

from nblite.templates.renderer import (
    get_builtin_templates,
    infer_template_format,
    render_template,
    render_template_string,
)

__all__ = [
    "render_template",
    "render_template_string",
    "infer_template_format",
    "get_builtin_templates",
    "get_global_templates_dir",
    "GITHUB_TEMPLATES_URL",
    "GITHUB_TEMPLATES_API_URL",
    "GITHUB_RAW_BASE_URL",
]

# URL for default templates repository
GITHUB_TEMPLATES_URL = "https://github.com/lukastk/nblite/tree/main/notebook-templates"
GITHUB_TEMPLATES_API_URL = "https://api.github.com/repos/lukastk/nblite/contents/notebook-templates"
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/lukastk/nblite/main/notebook-templates"


def get_global_templates_dir() -> Path:
    """
    Get the global templates directory path.

    Returns:
        Path to ~/.config/nblite/templates

    Example:
        >>> templates_dir = get_global_templates_dir()
        >>> print(templates_dir)
        /home/user/.config/nblite/templates
    """
    return Path.home() / ".config" / "nblite" / "templates"

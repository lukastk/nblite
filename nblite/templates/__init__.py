"""
Template handling for nblite.

This module handles notebook templates and Jinja2 rendering.
"""

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
]

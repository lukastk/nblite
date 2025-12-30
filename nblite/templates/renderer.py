"""
Template rendering for nblite.

Uses Jinja2 to render notebook templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

__all__ = ["render_template", "render_template_string"]


def render_template(
    template_path: Path | str,
    **context: Any,
) -> str:
    """
    Render a Jinja2 template file.

    Args:
        template_path: Path to the template file.
        **context: Variables to pass to the template.

    Returns:
        Rendered template as string.

    Example:
        >>> render_template(
        ...     "templates/notebook.pct.py.jinja",
        ...     module_name="utils",
        ...     author="John Doe"
        ... )
    """
    template_path = Path(template_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        autoescape=False,
        keep_trailing_newline=True,
    )

    template = env.get_template(template_path.name)
    return template.render(**context)


def render_template_string(
    template_string: str,
    **context: Any,
) -> str:
    """
    Render a Jinja2 template string.

    Args:
        template_string: Template content as string.
        **context: Variables to pass to the template.

    Returns:
        Rendered template as string.

    Example:
        >>> render_template_string(
        ...     "#|default_exp {{ module_name }}",
        ...     module_name="utils"
        ... )
        '#|default_exp utils'
    """
    template = Template(template_string)
    return template.render(**context)


def get_builtin_templates() -> dict[str, str]:
    """
    Get built-in notebook templates.

    Returns:
        Dictionary mapping template name to template content.
    """
    return {
        "default": """# %%
#|default_exp {{ module_name }}

# %% [markdown]
# # {{ title or module_name }}

# %%
#|export
""",
        "script": """# %%
#|default_exp {{ module_name }}
#|export_as_func true

# %%
#|top_export
from pathlib import Path

# %%
#|set_func_signature
def {{ function_name or 'main' }}({{ args or '' }}):
    ...

# %%
#|export
pass

# %%
#|func_return
None
""",
    }

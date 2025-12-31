"""
Template rendering for nblite.

Uses Jinja2 to render notebook templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

__all__ = ["render_template", "render_template_string", "infer_template_format"]


def infer_template_format(template_path: Path | str) -> str:
    """
    Infer the notebook format from a template file path.

    The format is determined by the extension before .jinja (if present):
    - .ipynb.jinja or .ipynb -> ipynb
    - .pct.py.jinja or .pct.py -> percent
    - .py.jinja or .py (but not .pct.py) -> percent

    Args:
        template_path: Path to the template file.

    Returns:
        Format string: "ipynb" or "percent"
    """
    name = Path(template_path).name.lower()

    # Strip .jinja suffix if present
    if name.endswith(".jinja"):
        name = name[:-6]

    # Check for specific formats
    if name.endswith(".ipynb"):
        return "ipynb"
    elif name.endswith(".pct.py"):
        return "percent"
    elif name.endswith(".py"):
        return "percent"

    # Default to percent (text-based format)
    return "percent"


def render_template(
    template_path: Path | str,
    dest_fmt: str | None = None,
    **context: Any,
) -> str:
    """
    Render a Jinja2 template file.

    The template format is inferred from the file extension:
    - .ipynb.jinja -> ipynb format
    - .pct.py.jinja -> percent format

    If dest_fmt is specified and differs from the template format,
    the rendered content will be converted.

    Args:
        template_path: Path to the template file.
        dest_fmt: Destination format (ipynb, percent). If None, uses template format.
        **context: Variables to pass to the template.

    Returns:
        Rendered template as string.

    Example:
        >>> # Render a percent template to ipynb format
        >>> render_template(
        ...     "templates/notebook.pct.py.jinja",
        ...     dest_fmt="ipynb",
        ...     module_name="utils",
        ... )
    """
    template_path = Path(template_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Infer source format from template extension
    source_fmt = infer_template_format(template_path)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        autoescape=False,
        keep_trailing_newline=True,
    )

    template = env.get_template(template_path.name)
    rendered = template.render(**context)

    # Convert format if needed
    if dest_fmt is not None and dest_fmt != source_fmt:
        from nblite.core.notebook import Notebook

        nb = Notebook.from_string(rendered, format=source_fmt)
        rendered = nb.to_string(format=dest_fmt)

    return rendered


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

    Built-in variables:
    - module_name: Module name for default_exp
    - title: Notebook title (optional)
    - no_export: If true, skip default_exp directive
    - pyproject: Contents of pyproject.toml (if exists)

    Custom variables can be passed via --var and used in templates.

    Returns:
        Dictionary mapping template name to template content.
    """
    return {
        "default": """# %%
{% if not no_export %}#|default_exp {{ module_name }}{% endif %}

# %% [markdown]
# # {{ title or module_name }}

# %%
#|export
""",
        "script": """# %%
{% if not no_export %}#|default_exp {{ module_name }}
{% endif %}#|export_as_func true

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

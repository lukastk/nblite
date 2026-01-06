"""New command for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nblite.cli._helpers import CONFIG_PATH_KEY, console
from nblite.cli.app import app


def _load_pyproject(project_root: Path | None) -> dict | None:
    """Load pyproject.toml as a dictionary if it exists."""
    if project_root is None:
        project_root = Path.cwd()

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore

    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def _find_template_in_dir(template_name: str, templates_dir: Path) -> Path | None:
    """
    Search for a template in a specific directory.

    Args:
        template_name: Name of the template (without .jinja extension)
        templates_dir: Directory to search in

    Returns:
        Path to template if found, None otherwise.
    """
    if not templates_dir.exists():
        return None

    # Try various extensions
    for ext in [".pct.py.jinja", ".ipynb.jinja", ".py.jinja", ".jinja", ""]:
        candidate = templates_dir / f"{template_name}{ext}"
        if candidate.exists():
            return candidate

    return None


def _find_template(
    template_name: str,
    project_root: Path | None,
    templates_folder: str = "templates",
) -> tuple[Path | None, str | None]:
    """
    Find a template by name.

    Searches in order (first match wins):
    1. Project templates folder (if project exists)
    2. Global templates folder (~/.config/nblite/templates)
    3. Built-in templates

    Args:
        template_name: Name of the template (without .jinja extension)
        project_root: Project root path
        templates_folder: Templates folder name within project

    Returns:
        Tuple of (template_path, builtin_content).
        If a file template is found, returns (path, None).
        If a builtin template is found, returns (None, content).
        If nothing found, returns (None, None).
    """
    from nblite.templates import get_builtin_templates, get_global_templates_dir

    # 1. Search in project templates folder (highest priority)
    if project_root is not None:
        templates_dir = project_root / templates_folder
        found = _find_template_in_dir(template_name, templates_dir)
        if found:
            return found, None

    # 2. Search in global templates folder
    global_templates_dir = get_global_templates_dir()
    found = _find_template_in_dir(template_name, global_templates_dir)
    if found:
        return found, None

    # 3. Search in built-in templates (lowest priority)
    builtins = get_builtin_templates()
    if template_name in builtins:
        return None, builtins[template_name]

    return None, None


def _infer_output_format(notebook_path: Path) -> str:
    """Infer the output format from the notebook path."""
    name = notebook_path.name.lower()
    if name.endswith(".pct.py"):
        return "percent"
    elif name.endswith(".ipynb"):
        return "ipynb"
    elif name.endswith(".py"):
        return "percent"
    # Default to ipynb
    return "ipynb"


def _parse_var_args(var_args: list[str]) -> dict[str, str]:
    """Parse key=value arguments into a dictionary."""
    result = {}
    for arg in var_args:
        if "=" not in arg:
            raise typer.BadParameter(f"Invalid variable format: '{arg}'. Expected 'key=value'.")
        key, value = arg.split("=", 1)
        result[key.strip()] = value.strip()
    return result


@app.command()
def new(
    ctx: typer.Context,
    notebook_path: Annotated[
        Path,
        typer.Argument(help="Path for the new notebook"),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Module name for default_exp"),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", "-t", help="Notebook title"),
    ] = None,
    template: Annotated[
        str | None,
        typer.Option("--template", help="Template to use (name or path)"),
    ] = None,
    no_export: Annotated[
        bool,
        typer.Option("--no-export", help="Don't include default_exp directive"),
    ] = False,
    var: Annotated[
        list[str] | None,
        typer.Option("--var", "-v", help="Template variable as key=value (can be repeated)"),
    ] = None,
) -> None:
    """Create a new notebook.

    Creates a notebook from a template. Templates can be:
    - Built-in: "default" or "script"
    - Custom: defined in project's templates folder
    - File path: direct path to a .jinja template file

    The output format is inferred from the notebook path:
    - .ipynb -> Jupyter notebook format
    - .pct.py -> Percent format

    Template variables available:
    - module_name: Module name (from --name or inferred from path)
    - title: Notebook title (from --title)
    - no_export: Whether to skip default_exp directive (from --no-export)
    - pyproject: Contents of pyproject.toml (if exists)
    - Any custom variables passed via --var key=value

    Examples:
        nbl new my_notebook.ipynb
        nbl new my_notebook.pct.py --template script
        nbl new my_notebook.ipynb --var author="John Doe" --var version="1.0"
    """
    from nblite.core.project import NbliteProject
    from nblite.templates import render_template, render_template_string

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    # Try to find project root
    project = None
    project_root = None
    templates_folder = "templates"
    try:
        project = NbliteProject.from_path(config_path)
        project_root = project.root_path
        notebook_path = project_root / notebook_path
        templates_folder = project.config.templates.folder
    except FileNotFoundError:
        notebook_path = Path.cwd() / notebook_path

    # Determine module name
    if name is None:
        name = notebook_path.stem
        if name.endswith(".pct"):
            name = name[:-4]

    # Determine output format from path
    output_fmt = _infer_output_format(notebook_path)

    # Parse custom variables
    custom_vars = _parse_var_args(var or [])

    # Load pyproject.toml
    pyproject = _load_pyproject(project_root)

    # Build template context
    context = {
        "module_name": name,
        "title": title,
        "no_export": no_export,
        "pyproject": pyproject,
        **custom_vars,
    }

    # Determine template to use
    # Use project config default if available, otherwise built-in "default"
    default_template = "default"
    if project is not None and project.config.templates.default:
        default_template = project.config.templates.default
    template_name = template or default_template

    # Check if template is a file path
    template_as_path = Path(template_name)
    if template_as_path.exists() or (project_root and (project_root / template_name).exists()):
        # Direct file path
        if not template_as_path.exists() and project_root:
            template_as_path = project_root / template_name
        content = render_template(template_as_path, dest_fmt=output_fmt, **context)
    else:
        # Search for template by name
        template_path, builtin_content = _find_template(
            template_name, project_root, templates_folder
        )

        if template_path is not None:
            # File template found
            content = render_template(template_path, dest_fmt=output_fmt, **context)
        elif builtin_content is not None:
            # Built-in template found (percent format)
            rendered = render_template_string(builtin_content, **context)
            # Convert if needed
            if output_fmt != "percent":
                from nblite.core.notebook import Notebook

                nb = Notebook.from_string(rendered, format="percent")
                content = nb.to_string(format=output_fmt)
            else:
                content = rendered
        else:
            console.print(f"[red]Error: Template '{template_name}' not found.[/red]")
            raise typer.Exit(1)

    # Write the notebook
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(content)

    console.print(f"[green]Created notebook: {notebook_path}[/green]")

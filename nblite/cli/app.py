"""
Main CLI application for nblite.

This module defines the `nbl` command and all subcommands.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Optional

import typer

if TYPE_CHECKING:
    from nblite.core.project import NbliteProject
from rich.console import Console
from rich.table import Table
from rich.text import Text

from nblite import __version__

app = typer.Typer(
    name="nbl",
    help="nblite - Notebook-driven Python package development tool",
    no_args_is_help=True,
)

console = Console()

# Global config path stored in context
CONFIG_PATH_KEY = "config_path"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"nblite version {__version__}")
        raise typer.Exit()


def get_project(ctx: typer.Context) -> "NbliteProject":
    """
    Get the NbliteProject using the config path from context.

    Args:
        ctx: Typer context containing optional config_path

    Returns:
        NbliteProject instance

    Raises:
        typer.Exit: If project cannot be loaded
    """
    from nblite.core.project import NbliteProject

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    try:
        return NbliteProject.from_path(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Path to nblite.toml config file",
            envvar="NBLITE_CONFIG",
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """nblite - Notebook-driven Python package development tool."""
    ctx.ensure_object(dict)
    if config is not None:
        ctx.obj[CONFIG_PATH_KEY] = config


@app.command()
def init(
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Module name (default: directory name)"),
    ] = None,
    path: Annotated[
        Optional[Path],
        typer.Option("--path", "-p", help="Project path (default: current directory)"),
    ] = None,
    use_defaults: Annotated[
        bool,
        typer.Option("--use-defaults", help="Use defaults without prompting"),
    ] = False,
) -> None:
    """Initialize a new nblite project."""
    project_path = path or Path.cwd()
    project_path = project_path.resolve()

    if name is None:
        name = project_path.name

    config_path = project_path / "nblite.toml"
    if config_path.exists() and not use_defaults:
        console.print("[yellow]nblite.toml already exists[/yellow]")
        raise typer.Exit(1)

    # Create default config
    config_content = f'''# nblite configuration
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "{name}"
format = "module"
'''

    # Create directories
    (project_path / "nbs").mkdir(exist_ok=True)
    (project_path / name).mkdir(exist_ok=True)
    (project_path / name / "__init__.py").touch()

    config_path.write_text(config_content)

    console.print(f"[green]Initialized nblite project: {name}[/green]")
    console.print(f"  Config: {config_path}")
    console.print(f"  Notebooks: {project_path / 'nbs'}")
    console.print(f"  Package: {project_path / name}")


@app.command()
def new(
    ctx: typer.Context,
    notebook_path: Annotated[
        Path,
        typer.Argument(help="Path for the new notebook"),
    ],
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Module name for default_exp"),
    ] = None,
    title: Annotated[
        Optional[str],
        typer.Option("--title", "-t", help="Notebook title"),
    ] = None,
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template to use"),
    ] = None,
    no_export: Annotated[
        bool,
        typer.Option("--no-export", help="Don't include default_exp directive"),
    ] = False,
) -> None:
    """Create a new notebook."""
    from nblite.core.project import NbliteProject

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    # Try to find project root
    try:
        project = NbliteProject.from_path(config_path)
        notebook_path = project.root_path / notebook_path
    except FileNotFoundError:
        notebook_path = Path.cwd() / notebook_path

    # Determine module name
    if name is None:
        name = notebook_path.stem
        if name.endswith(".pct"):
            name = name[:-4]

    # Create notebook content
    cells = []

    # Add default_exp directive
    if not no_export:
        cells.append({
            "cell_type": "code",
            "source": f"#|default_exp {name}",
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        })

    # Add title if specified
    if title:
        cells.append({
            "cell_type": "markdown",
            "source": f"# {title}",
            "metadata": {},
        })

    nb_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(nb_content, indent=2))

    console.print(f"[green]Created notebook: {notebook_path}[/green]")


@app.command()
def export(
    ctx: typer.Context,
    notebooks: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Specific notebooks to export"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be exported without doing it"),
    ] = False,
) -> None:
    """Run the export pipeline."""
    project = get_project(ctx)

    if dry_run:
        console.print("[blue]Dry run - would export:[/blue]")
        nbs = project.get_notebooks()
        for nb in nbs:
            twins = project.get_notebook_twins(nb)
            console.print(f"  {nb.source_path}")
            for twin in twins:
                console.print(f"    -> {twin}")
        return

    result = project.export(notebooks=notebooks)

    if result.success:
        console.print("[green]Export completed successfully[/green]")
        for f in result.files_created:
            console.print(f"  [green]+[/green] {f}")
    else:
        console.print("[red]Export completed with errors[/red]")
        for error in result.errors:
            console.print(f"  [red]Error:[/red] {error}")
        raise typer.Exit(1)


@app.command()
def clean(
    ctx: typer.Context,
    notebooks: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Specific notebooks to clean"),
    ] = None,
    remove_outputs: Annotated[
        bool,
        typer.Option("-O", "--remove-outputs", help="Remove all outputs from code cells"),
    ] = False,
    remove_execution_counts: Annotated[
        bool,
        typer.Option("-e", "--remove-execution-counts", help="Remove execution counts from code cells"),
    ] = False,
    remove_cell_metadata: Annotated[
        bool,
        typer.Option("--remove-cell-metadata", help="Remove cell-level metadata"),
    ] = False,
    remove_notebook_metadata: Annotated[
        bool,
        typer.Option("--remove-notebook-metadata", help="Remove notebook-level metadata"),
    ] = False,
    remove_kernel_info: Annotated[
        bool,
        typer.Option("--remove-kernel-info", help="Remove kernel specification"),
    ] = False,
    preserve_cell_ids: Annotated[
        bool,
        typer.Option("--preserve-cell-ids/--remove-cell-ids", help="Preserve or remove cell IDs"),
    ] = True,
    remove_output_metadata: Annotated[
        bool,
        typer.Option("--remove-output-metadata", help="Remove metadata from outputs"),
    ] = False,
    remove_output_execution_counts: Annotated[
        bool,
        typer.Option("--remove-output-execution-counts", help="Remove execution counts from output results"),
    ] = False,
    keep_only: Annotated[
        Optional[str],
        typer.Option("--keep-only", help="Keep only these metadata keys (comma-separated)"),
    ] = None,
) -> None:
    """Clean notebooks by removing outputs and metadata.

    By default, no changes are made unless options are specified.
    Options can also be configured in nblite.toml under [clean].

    Examples:
        nbl clean -O                    # Remove outputs
        nbl clean -O -e                 # Remove outputs and execution counts
        nbl clean --remove-cell-metadata
    """
    project = get_project(ctx)

    # Parse keep_only into list if provided
    keep_only_list = None
    if keep_only:
        keep_only_list = [k.strip() for k in keep_only.split(",")]

    # Pass CLI options as overrides (only if they differ from defaults)
    # For flags, we pass them if they're True (user explicitly set them)
    project.clean(
        notebooks=notebooks,
        remove_outputs=remove_outputs if remove_outputs else None,
        remove_execution_counts=remove_execution_counts if remove_execution_counts else None,
        remove_cell_metadata=remove_cell_metadata if remove_cell_metadata else None,
        remove_notebook_metadata=remove_notebook_metadata if remove_notebook_metadata else None,
        remove_kernel_info=remove_kernel_info if remove_kernel_info else None,
        preserve_cell_ids=preserve_cell_ids if not preserve_cell_ids else None,  # Only pass if False
        remove_output_metadata=remove_output_metadata if remove_output_metadata else None,
        remove_output_execution_counts=remove_output_execution_counts if remove_output_execution_counts else None,
        keep_only_metadata=keep_only_list,
    )
    console.print("[green]Notebooks cleaned[/green]")


@app.command()
def convert(
    input_path: Annotated[
        Path,
        typer.Argument(help="Input notebook path"),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(help="Output notebook path"),
    ],
    from_format: Annotated[
        Optional[str],
        typer.Option("--from", help="Input format (auto-detected if omitted)"),
    ] = None,
    to_format: Annotated[
        Optional[str],
        typer.Option("--to", help="Output format (auto-detected if omitted)"),
    ] = None,
) -> None:
    """Convert notebook between formats."""
    from nblite.core.notebook import Format, Notebook
    from nblite.export.pipeline import export_notebook_to_notebook

    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input_path}[/red]")
        raise typer.Exit(1)

    nb = Notebook.from_file(input_path, format=from_format)
    export_notebook_to_notebook(nb, output_path, format=to_format)

    console.print(f"[green]Converted {input_path} -> {output_path}[/green]")


@app.command("from-module")
def from_module_cmd(
    input_path: Annotated[
        Path,
        typer.Argument(help="Path to Python module file or directory"),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(help="Output notebook path or directory"),
    ],
    module_name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Module name for default_exp (default: file stem). Only for single file."),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: ipynb or percent"),
    ] = "ipynb",
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Process subdirectories recursively (for directory input)"),
    ] = True,
    include_init: Annotated[
        bool,
        typer.Option("--include-init", help="Include __init__.py files"),
    ] = False,
    include_dunders: Annotated[
        bool,
        typer.Option("--include-dunders", help="Include __*.py files (like __main__.py)"),
    ] = False,
    include_hidden: Annotated[
        bool,
        typer.Option("--include-hidden", help="Include hidden files/directories (starting with .)"),
    ] = False,
) -> None:
    """Convert Python module(s) to notebook(s).

    Can convert a single Python file or all Python files in a directory.

    For single file:
        Parses the Python file and creates a notebook with:
        - A default_exp directive
        - Code cells for imports
        - Code cells for each function/class with #|export directive
        - Markdown cells for module docstrings

    For directory:
        Converts all .py files, preserving directory structure.

    Example:
        nbl from-module utils.py nbs/utils.ipynb
        nbl from-module lib/core.py nbs/core.ipynb --name core
        nbl from-module src/ nbs/ --recursive
        nbl from-module mypackage/ notebooks/ --include-init
    """
    from nblite.convert import module_to_notebook, modules_to_notebooks

    if not input_path.exists():
        console.print(f"[red]Error: Path not found: {input_path}[/red]")
        raise typer.Exit(1)

    if output_format not in ("ipynb", "percent"):
        console.print(f"[red]Error: Invalid format '{output_format}'. Use 'ipynb' or 'percent'.[/red]")
        raise typer.Exit(1)

    try:
        if input_path.is_dir():
            # Directory mode
            if module_name is not None:
                console.print("[yellow]Warning: --name is ignored when converting a directory[/yellow]")

            created = modules_to_notebooks(
                input_path,
                output_path,
                format=output_format,
                recursive=recursive,
                exclude_init=not include_init,
                exclude_dunders=not include_dunders,
                exclude_hidden=not include_hidden,
            )
            console.print(f"[green]Created {len(created)} notebook(s) in {output_path}[/green]")
            for path in created:
                console.print(f"  {path}")
        else:
            # Single file mode
            module_to_notebook(
                input_path,
                output_path,
                module_name=module_name,
                format=output_format,
            )
            console.print(f"[green]Created notebook: {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info(ctx: typer.Context) -> None:
    """Show project information."""
    project = get_project(ctx)

    console.print(f"[bold]Project:[/bold] {project.root_path}")
    console.print()

    # Show code locations
    table = Table(title="Code Locations")
    table.add_column("Key", style="cyan")
    table.add_column("Path")
    table.add_column("Format")
    table.add_column("Files")

    for key, cl in project.code_locations.items():
        files = cl.get_files()
        table.add_row(
            key,
            str(cl.relative_path),
            cl.format.value,
            str(len(files)),
        )

    console.print(table)

    # Show export pipeline
    if project.config.export_pipeline:
        console.print()
        console.print("[bold]Export Pipeline:[/bold]")
        for rule in project.config.export_pipeline:
            console.print(f"  {rule.from_key} -> {rule.to_key}")


@app.command("list")
def list_files(
    ctx: typer.Context,
    code_location: Annotated[
        Optional[str],
        typer.Argument(help="Code location to list (all if omitted)"),
    ] = None,
) -> None:
    """List notebooks and files in the project."""
    project = get_project(ctx)

    locations = project.code_locations.values()
    if code_location:
        try:
            locations = [project.get_code_location(code_location)]
        except KeyError:
            console.print(f"[red]Unknown code location: {code_location}[/red]")
            raise typer.Exit(1)

    for cl in locations:
        console.print(f"[bold cyan]{cl.key}[/bold cyan] ({cl.relative_path}):")
        files = cl.get_files()
        for f in files:
            rel_path = f.relative_to(cl.path)
            console.print(f"  {rel_path}")
        if not files:
            console.print("  [dim](no files)[/dim]")
        console.print()


@app.command("install-hooks")
def install_hooks_cmd(ctx: typer.Context) -> None:
    """Install git hooks for the project."""
    from nblite.git.hooks import install_hooks

    project = get_project(ctx)

    try:
        install_hooks(project)
        console.print("[green]Git hooks installed[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("uninstall-hooks")
def uninstall_hooks_cmd(ctx: typer.Context) -> None:
    """Remove git hooks for the project."""
    from nblite.git.hooks import uninstall_hooks

    project = get_project(ctx)
    uninstall_hooks(project)
    console.print("[green]Git hooks removed[/green]")


@app.command("validate")
def validate_cmd(ctx: typer.Context) -> None:
    """Validate git staging state."""
    from nblite.git.staging import validate_staging

    project = get_project(ctx)

    result = validate_staging(project)

    if result.warnings:
        for warning in result.warnings:
            console.print(f"[yellow]Warning:[/yellow] {warning}")

    if result.errors:
        for error in result.errors:
            console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(1)

    if result.valid and not result.warnings:
        console.print("[green]Staging is valid[/green]")


@app.command("hook")
def hook_cmd(
    ctx: typer.Context,
    hook_name: Annotated[
        str,
        typer.Argument(help="Hook name (pre-commit, post-commit)"),
    ],
) -> None:
    """Run a git hook (internal use)."""
    from nblite.core.project import NbliteProject

    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    try:
        project = NbliteProject.from_path(config_path)
    except FileNotFoundError:
        # Not in a project, silently exit
        return

    if hook_name == "pre-commit":
        # Auto-clean and validate
        if project.config.git.auto_clean:
            project.clean()

        if project.config.git.auto_export:
            project.export()

        if project.config.git.validate_staging:
            from nblite.git.staging import validate_staging
            result = validate_staging(project)
            if not result.valid:
                for error in result.errors:
                    console.print(f"[red]Error:[/red] {error}", err=True)
                raise typer.Exit(1)


def _run_fill(
    notebooks: list[Path] | None,
    code_locations: list[str] | None,
    timeout: int | None,
    n_workers: int,
    fill_unchanged: bool,
    remove_outputs_first: bool,
    exclude_dunders: bool,
    exclude_hidden: bool,
    dry_run: bool,
    silent: bool,
    config_path: Path | None = None,
) -> int:
    """
    Internal fill implementation shared by fill and test commands.

    Returns exit code (0 = success, 1 = error).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text

    from nblite.config.schema import CodeLocationFormat
    from nblite.core.notebook import Notebook
    from nblite.core.project import NbliteProject
    from nblite.fill import FillResult, FillStatus, fill_notebook, has_notebook_changed

    try:
        project = NbliteProject.from_path(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Collect notebooks to fill
    nbs_to_fill: list[Path] = []

    if notebooks:
        # Use specified notebooks
        for nb_path in notebooks:
            resolved = project.root_path / nb_path if not nb_path.is_absolute() else nb_path
            if resolved.exists():
                nbs_to_fill.append(resolved)
            else:
                console.print(f"[yellow]Warning: Notebook not found: {nb_path}[/yellow]")
    else:
        # Get from code locations
        fill_config = project.config.fill
        locations_to_fill = code_locations or fill_config.code_locations

        for key, cl in project.code_locations.items():
            # Only fill ipynb notebooks
            if cl.format != CodeLocationFormat.IPYNB:
                continue

            # Check if we should include this location
            if locations_to_fill is not None and key not in locations_to_fill:
                continue

            # Get notebooks from this location
            nbs = cl.get_notebooks(
                ignore_dunders=exclude_dunders,
                ignore_hidden=exclude_hidden,
            )

            for nb in nbs:
                if nb.source_path:
                    nbs_to_fill.append(nb.source_path)

    if not nbs_to_fill:
        console.print("[yellow]No notebooks to fill[/yellow]")
        return 0

    # Track results
    task_statuses: dict[Path, tuple[str, str]] = {}
    results: list[FillResult] = []

    # Initialize status tracking
    for nb_path in nbs_to_fill:
        task_statuses[nb_path] = ("...", "Pending")

    # Filter unchanged notebooks if not filling unchanged
    to_process: list[Path] = []
    if not fill_unchanged:
        for nb_path in nbs_to_fill:
            try:
                nb = Notebook.from_file(nb_path)
                if not has_notebook_changed(nb):
                    task_statuses[nb_path] = ("skip", "Skipped (unchanged)")
                    results.append(FillResult(
                        status=FillStatus.SKIPPED,
                        path=nb_path,
                        message="Skipped (unchanged)",
                    ))
                    continue
            except Exception:
                pass
            to_process.append(nb_path)
    else:
        to_process = list(nbs_to_fill)

    # Build status table
    def make_table() -> Table:
        table = Table(title="Fill Progress", show_header=True)
        table.add_column("Status", width=6)
        table.add_column("Notebook")
        table.add_column("Message")

        for nb_path in nbs_to_fill:
            status, msg = task_statuses.get(nb_path, ("...", "Pending"))
            rel_path = nb_path.relative_to(project.root_path) if nb_path.is_relative_to(project.root_path) else nb_path

            if status == "ok":
                status_str = "[green]ok[/green]"
            elif status == "skip":
                status_str = "[yellow]skip[/yellow]"
            elif status == "err":
                status_str = "[red]err[/red]"
            elif status == "run":
                status_str = "[blue]run[/blue]"
            else:
                status_str = "[dim]...[/dim]"

            table.add_row(status_str, str(rel_path), msg)

        return table

    # Process notebooks
    def process_one(nb_path: Path) -> FillResult:
        task_statuses[nb_path] = ("run", "Executing...")
        result = fill_notebook(
            nb_path,
            timeout=timeout,
            dry_run=dry_run,
            remove_outputs_first=remove_outputs_first,
        )
        if result.status == FillStatus.SUCCESS:
            task_statuses[nb_path] = ("ok", "Success")
        elif result.status == FillStatus.SKIPPED:
            task_statuses[nb_path] = ("skip", result.message)
        else:
            task_statuses[nb_path] = ("err", result.message[:50])
        return result

    if silent:
        # Silent mode - no output during execution
        if n_workers <= 1:
            for nb_path in to_process:
                results.append(process_one(nb_path))
        else:
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = {executor.submit(process_one, p): p for p in to_process}
                for future in as_completed(futures):
                    results.append(future.result())
    else:
        # Progress display mode
        with Live(make_table(), refresh_per_second=4, console=console) as live:
            if n_workers <= 1:
                for nb_path in to_process:
                    results.append(process_one(nb_path))
                    live.update(make_table())
            else:
                with ThreadPoolExecutor(max_workers=n_workers) as executor:
                    futures = {executor.submit(process_one, p): p for p in to_process}
                    for future in as_completed(futures):
                        results.append(future.result())
                        live.update(make_table())

    # Summary
    success_count = sum(1 for r in results if r.status == FillStatus.SUCCESS)
    skipped_count = sum(1 for r in results if r.status == FillStatus.SKIPPED)
    error_count = sum(1 for r in results if r.status == FillStatus.ERROR)

    console.print()
    if dry_run:
        console.print("[blue]Dry run completed (no files modified)[/blue]")

    console.print(f"[green]{success_count} succeeded[/green], "
                  f"[yellow]{skipped_count} skipped[/yellow], "
                  f"[red]{error_count} failed[/red]")

    # Show errors
    if error_count > 0:
        console.print()
        console.print("[red]Errors:[/red]")
        for r in results:
            if r.status == FillStatus.ERROR:
                rel_path = r.path.relative_to(project.root_path) if r.path and r.path.is_relative_to(project.root_path) else r.path
                # Use Text.from_ansi() to properly render ANSI codes from Jupyter tracebacks
                error_text = Text.from_ansi(f"  {rel_path}: {r.message}")
                console.print(error_text)
        return 1

    return 0


@app.command()
def fill(
    ctx: typer.Context,
    notebooks: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Specific notebooks to fill (all ipynb if omitted)"),
    ] = None,
    code_locations: Annotated[
        Optional[list[str]],
        typer.Option("--code-location", "-c", help="Code locations to fill"),
    ] = None,
    timeout: Annotated[
        Optional[int],
        typer.Option("--timeout", "-t", help="Cell execution timeout in seconds"),
    ] = None,
    n_workers: Annotated[
        int,
        typer.Option("--workers", "-w", help="Number of parallel workers"),
    ] = 4,
    fill_unchanged: Annotated[
        bool,
        typer.Option("--fill-unchanged", help="Fill notebooks even if unchanged"),
    ] = False,
    remove_outputs_first: Annotated[
        bool,
        typer.Option("--remove-outputs", help="Remove existing outputs before fill"),
    ] = False,
    include_dunders: Annotated[
        bool,
        typer.Option("--include-dunders", help="Include __* notebooks"),
    ] = False,
    include_hidden: Annotated[
        bool,
        typer.Option("--include-hidden", help="Include .* notebooks"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Execute but don't save results"),
    ] = False,
    silent: Annotated[
        bool,
        typer.Option("--silent", "-s", help="Suppress progress output"),
    ] = False,
) -> None:
    """Execute notebooks and fill cell outputs.

    Runs all cells in ipynb notebooks and saves the outputs. Uses a hash
    to track changes and skip unchanged notebooks (use --fill-unchanged
    to override).

    Respects skip directives:
    - #|eval: false - Skip a single cell
    - #|skip_evals - Skip all following cells
    - #|skip_evals_stop - Resume execution
    """
    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None
    exit_code = _run_fill(
        notebooks=notebooks,
        code_locations=code_locations,
        timeout=timeout,
        n_workers=n_workers,
        fill_unchanged=fill_unchanged,
        remove_outputs_first=remove_outputs_first,
        exclude_dunders=not include_dunders,
        exclude_hidden=not include_hidden,
        dry_run=dry_run,
        silent=silent,
        config_path=config_path,
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command()
def test(
    ctx: typer.Context,
    notebooks: Annotated[
        Optional[list[Path]],
        typer.Argument(help="Specific notebooks to test (all ipynb if omitted)"),
    ] = None,
    code_locations: Annotated[
        Optional[list[str]],
        typer.Option("--code-location", "-c", help="Code locations to test"),
    ] = None,
    timeout: Annotated[
        Optional[int],
        typer.Option("--timeout", "-t", help="Cell execution timeout in seconds"),
    ] = None,
    n_workers: Annotated[
        int,
        typer.Option("--workers", "-w", help="Number of parallel workers"),
    ] = 4,
    fill_unchanged: Annotated[
        bool,
        typer.Option("--fill-unchanged", help="Test notebooks even if unchanged"),
    ] = False,
    include_dunders: Annotated[
        bool,
        typer.Option("--include-dunders", help="Include __* notebooks"),
    ] = False,
    include_hidden: Annotated[
        bool,
        typer.Option("--include-hidden", help="Include .* notebooks"),
    ] = False,
    silent: Annotated[
        bool,
        typer.Option("--silent", "-s", help="Suppress progress output"),
    ] = False,
) -> None:
    """Test that notebooks execute without errors (dry run).

    This is an alias for `nbl fill --dry-run`. It executes all cells
    but does not save the results, making it useful for CI/CD pipelines
    to verify notebooks run correctly.
    """
    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None
    exit_code = _run_fill(
        notebooks=notebooks,
        code_locations=code_locations,
        timeout=timeout,
        n_workers=n_workers,
        fill_unchanged=fill_unchanged,
        remove_outputs_first=False,
        exclude_dunders=not include_dunders,
        exclude_hidden=not include_hidden,
        dry_run=True,  # Always dry run for test
        silent=silent,
        config_path=config_path,
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command()
def readme(
    ctx: typer.Context,
    notebook_path: Annotated[
        Optional[Path],
        typer.Argument(help="Path to notebook (uses config readme_nb_path if omitted)"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output path (default: README.md in project root)"),
    ] = None,
) -> None:
    """Generate README.md from a notebook.

    Converts the specified notebook to markdown, filtering out cells
    with #|hide directive. The notebook path can be specified on the
    command line or in nblite.toml as readme_nb_path.

    Example nblite.toml:
        readme_nb_path = "nbs/index.ipynb"
    """
    from nblite.readme import generate_readme

    project = get_project(ctx)

    # Determine notebook path
    if notebook_path is None:
        if project.config.readme_nb_path is None:
            console.print("[red]Error: No notebook specified.[/red]")
            console.print("Either pass a notebook path or set readme_nb_path in nblite.toml")
            raise typer.Exit(1)
        notebook_path = project.root_path / project.config.readme_nb_path
    else:
        if not notebook_path.is_absolute():
            notebook_path = project.root_path / notebook_path

    if not notebook_path.exists():
        console.print(f"[red]Error: Notebook not found: {notebook_path}[/red]")
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = project.root_path / "README.md"
    elif not output.is_absolute():
        output = project.root_path / output

    generate_readme(notebook_path, output)
    console.print(f"[green]Generated {output}[/green]")


@app.command()
def prepare(
    ctx: typer.Context,
    skip_export: Annotated[
        bool,
        typer.Option("--skip-export", help="Skip export step"),
    ] = False,
    skip_clean: Annotated[
        bool,
        typer.Option("--skip-clean", help="Skip clean step"),
    ] = False,
    skip_fill: Annotated[
        bool,
        typer.Option("--skip-fill", help="Skip fill step"),
    ] = False,
    skip_readme: Annotated[
        bool,
        typer.Option("--skip-readme", help="Skip readme step"),
    ] = False,
    clean_outputs: Annotated[
        bool,
        typer.Option("--clean-outputs", help="Remove outputs during clean"),
    ] = False,
    fill_workers: Annotated[
        int,
        typer.Option("--fill-workers", "-w", help="Number of fill workers"),
    ] = 4,
    fill_unchanged: Annotated[
        bool,
        typer.Option("--fill-unchanged", help="Fill notebooks even if unchanged"),
    ] = False,
) -> None:
    """Run export, clean, fill, and readme in sequence.

    This is a convenience command that runs the full preparation
    pipeline for a project:
    1. Export notebooks (nbl export)
    2. Clean notebooks (nbl clean)
    3. Fill notebooks (nbl fill)
    4. Generate README (nbl readme) - only if readme_nb_path is configured

    Use --skip-* options to skip individual steps.
    """
    from nblite.readme import generate_readme

    project = get_project(ctx)
    config_path = ctx.obj.get(CONFIG_PATH_KEY) if ctx.obj else None

    # Step 1: Export
    if not skip_export:
        console.print("[bold]Step 1: Export[/bold]")
        result = project.export()
        if result.success:
            console.print(f"  [green]Exported {len(result.files_created)} files[/green]")
        else:
            console.print("[red]  Export failed[/red]")
            for error in result.errors:
                console.print(f"  [red]{error}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[dim]Step 1: Export (skipped)[/dim]")

    # Step 2: Clean
    if not skip_clean:
        console.print("[bold]Step 2: Clean[/bold]")
        project.clean(remove_outputs=clean_outputs if clean_outputs else None)
        console.print("  [green]Cleaned notebooks[/green]")
    else:
        console.print("[dim]Step 2: Clean (skipped)[/dim]")

    # Step 3: Fill
    if not skip_fill:
        console.print("[bold]Step 3: Fill[/bold]")
        exit_code = _run_fill(
            notebooks=None,
            code_locations=None,
            timeout=None,
            n_workers=fill_workers,
            fill_unchanged=fill_unchanged,
            remove_outputs_first=False,
            exclude_dunders=True,
            exclude_hidden=True,
            dry_run=False,
            silent=False,
            config_path=config_path,
        )
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        console.print("[dim]Step 3: Fill (skipped)[/dim]")

    # Step 4: README
    if not skip_readme and project.config.readme_nb_path:
        console.print("[bold]Step 4: README[/bold]")
        notebook_path = project.root_path / project.config.readme_nb_path
        if notebook_path.exists():
            output_path = project.root_path / "README.md"
            generate_readme(notebook_path, output_path)
            console.print(f"  [green]Generated {output_path}[/green]")
        else:
            console.print(f"  [yellow]Warning: readme notebook not found: {notebook_path}[/yellow]")
    elif skip_readme:
        console.print("[dim]Step 4: README (skipped)[/dim]")
    else:
        console.print("[dim]Step 4: README (no readme_nb_path configured)[/dim]")

    console.print()
    console.print("[green]Prepare completed![/green]")


@app.command("render-docs")
def render_docs_cmd(
    ctx: typer.Context,
    output_folder: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output folder (default: _docs)"),
    ] = None,
    generator: Annotated[
        Optional[str],
        typer.Option("--generator", "-g", help="Documentation generator (mkdocs, jupyterbook, quarto)"),
    ] = None,
    docs_cl: Annotated[
        Optional[str],
        typer.Option("--docs-cl", "-d", help="Code location to generate docs from"),
    ] = None,
) -> None:
    """Render documentation for the project.

    Generates documentation from notebooks using the specified generator.
    The generator can be mkdocs (default), jupyterbook, or quarto.

    Requires the appropriate documentation tool to be installed:
    - mkdocs: pip install mkdocs mkdocs-material mkdocs-jupyter
    - jupyterbook: pip install jupyter-book
    - quarto: Install from https://quarto.org/

    Example:
        nbl render-docs                    # Use default generator
        nbl render-docs -g quarto          # Use Quarto
        nbl render-docs -o docs_output     # Custom output folder
    """
    from tempfile import TemporaryDirectory

    from nblite.docs import get_generator

    project = get_project(ctx)

    # Determine generator
    gen_name = generator or project.config.docs_generator
    console.print(f"[bold]Using {gen_name} generator[/bold]")

    # Get docs code location
    docs_code_location = docs_cl or project.config.docs_cl or project.config.docs.code_location
    if not docs_code_location:
        console.print("[red]Error: No documentation code location configured.[/red]")
        console.print("Set docs_cl in nblite.toml or pass --docs-cl parameter.")
        raise typer.Exit(1)

    # Override config if docs_cl passed
    if docs_cl:
        project.config.docs_cl = docs_cl

    # Get output folder
    final_dir = output_folder or project.root_path / project.config.docs.output_folder

    try:
        gen = get_generator(gen_name)

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            console.print("[blue]Preparing documentation...[/blue]")
            gen.prepare(project, tmp_path)

            console.print("[blue]Building documentation...[/blue]")
            gen.build(tmp_path, final_dir)

        console.print(f"[green]Documentation generated at {final_dir}[/green]")
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print(f"Make sure {gen_name} is installed.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("preview-docs")
def preview_docs_cmd(
    ctx: typer.Context,
    generator: Annotated[
        Optional[str],
        typer.Option("--generator", "-g", help="Documentation generator (mkdocs, jupyterbook, quarto)"),
    ] = None,
    docs_cl: Annotated[
        Optional[str],
        typer.Option("--docs-cl", "-d", help="Code location to generate docs from"),
    ] = None,
) -> None:
    """Preview documentation with live reload.

    Starts a local server to preview documentation. Changes to notebooks
    may require restarting the preview.

    The generator can be mkdocs (default), jupyterbook, or quarto.

    Example:
        nbl preview-docs                   # Use default generator
        nbl preview-docs -g quarto         # Use Quarto
    """
    from tempfile import TemporaryDirectory

    from nblite.docs import get_generator

    project = get_project(ctx)

    # Determine generator
    gen_name = generator or project.config.docs_generator
    console.print(f"[bold]Using {gen_name} generator[/bold]")

    # Get docs code location
    docs_code_location = docs_cl or project.config.docs_cl or project.config.docs.code_location
    if not docs_code_location:
        console.print("[red]Error: No documentation code location configured.[/red]")
        console.print("Set docs_cl in nblite.toml or pass --docs-cl parameter.")
        raise typer.Exit(1)

    # Override config if docs_cl passed
    if docs_cl:
        project.config.docs_cl = docs_cl

    try:
        gen = get_generator(gen_name)

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            console.print("[blue]Preparing documentation...[/blue]")
            gen.prepare(project, tmp_path)

            console.print("[blue]Starting preview server...[/blue]")
            console.print("Press Ctrl+C to stop")
            gen.preview(tmp_path)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print(f"Make sure {gen_name} is installed.")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Preview stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

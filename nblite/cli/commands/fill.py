"""Fill and test commands for nblite CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table
from rich.text import Text

from nblite import DISABLE_NBLITE_EXPORT_ENV_VAR
from nblite.cli._helpers import console
from nblite.cli.app import app


def _run_fill(
    notebooks: list[Path] | None,
    code_locations: list[str] | None,
    timeout: int | None,
    n_workers: int,
    fill_unchanged: bool,
    remove_outputs_first: bool,
    clean: bool,
    save_hash: bool,
    exclude_dunders: bool,
    exclude_hidden: bool,
    dry_run: bool,
    silent: bool,
    allow_export: bool = False,
    config_path: Path | None = None,
) -> int:
    """
    Internal fill implementation shared by fill and test commands.

    Returns exit code (0 = success, 1 = error).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from rich.live import Live

    from nblite.config.schema import CodeLocationFormat
    from nblite.core.notebook import Notebook
    from nblite.core.project import NbliteProject
    from nblite.fill import FillResult, FillStatus, fill_notebook, has_notebook_changed

    # Disable export during fill by default (can interfere with notebook execution)
    prev_disable_export = os.environ.get(DISABLE_NBLITE_EXPORT_ENV_VAR)
    if not allow_export:
        os.environ[DISABLE_NBLITE_EXPORT_ENV_VAR] = "true"

    try:
        project = NbliteProject.from_path(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        # Restore environment variable before returning
        if prev_disable_export is None:
            os.environ.pop(DISABLE_NBLITE_EXPORT_ENV_VAR, None)
        else:
            os.environ[DISABLE_NBLITE_EXPORT_ENV_VAR] = prev_disable_export
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
                    results.append(
                        FillResult(
                            status=FillStatus.SKIPPED,
                            path=nb_path,
                            message="Skipped (unchanged)",
                        )
                    )
                    continue
            except Exception:
                pass  # If we can't check, process anyway
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
            rel_path = (
                nb_path.relative_to(project.root_path)
                if nb_path.is_relative_to(project.root_path)
                else nb_path
            )

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
            clean=clean,
            save_hash=save_hash,
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

    console.print(
        f"[green]{success_count} succeeded[/green], "
        f"[yellow]{skipped_count} skipped[/yellow], "
        f"[red]{error_count} failed[/red]"
    )

    # Show errors
    if error_count > 0:
        console.print()
        console.print("[red]Errors:[/red]")
        for r in results:
            if r.status == FillStatus.ERROR:
                rel_path = (
                    r.path.relative_to(project.root_path)
                    if r.path and r.path.is_relative_to(project.root_path)
                    else r.path
                )
                # Use Text.from_ansi() to properly render ANSI codes from Jupyter tracebacks
                error_text = Text.from_ansi(f"  {rel_path}: {r.message}")
                console.print(error_text)
        exit_code = 1
    else:
        exit_code = 0

    # Restore environment variable
    if prev_disable_export is None:
        os.environ.pop(DISABLE_NBLITE_EXPORT_ENV_VAR, None)
    else:
        os.environ[DISABLE_NBLITE_EXPORT_ENV_VAR] = prev_disable_export

    return exit_code


@app.command()
def fill(
    ctx: typer.Context,
    notebooks: Annotated[
        list[Path] | None,
        typer.Argument(help="Specific notebooks to fill (all ipynb if omitted)"),
    ] = None,
    code_locations: Annotated[
        list[str] | None,
        typer.Option("--code-location", "-c", help="Code locations to fill"),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", "-t", help="Cell execution timeout in seconds"),
    ] = None,
    n_workers: Annotated[
        int,
        typer.Option("--workers", "-w", help="Number of parallel workers"),
    ] = 4,
    fill_unchanged: Annotated[
        bool,
        typer.Option("--fill-unchanged", "-f", help="Fill notebooks even if unchanged"),
    ] = False,
    remove_outputs_first: Annotated[
        bool,
        typer.Option("--remove-outputs", help="Remove existing outputs before fill"),
    ] = False,
    clean: Annotated[
        bool,
        typer.Option(
            "--clean/--no-clean", help="Clean notebook after fill (removes execution metadata)"
        ),
    ] = True,
    save_hash: Annotated[
        bool,
        typer.Option("--hash/--no-hash", help="Save notebook hash for change detection"),
    ] = True,
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
    allow_export: Annotated[
        bool,
        typer.Option("--allow-export", help="Allow nbl_export() during fill (disabled by default)"),
    ] = False,
) -> None:
    """Execute notebooks and fill cell outputs.

    Runs all cells in ipynb notebooks and saves the outputs. Uses a hash
    to track changes and skip unchanged notebooks (use --fill-unchanged
    to override).

    By default, notebooks are cleaned after execution to remove execution
    metadata (timestamps, execution counts) for cleaner VCS diffs. Use
    --no-clean to disable this.

    By default, nbl_export() calls in notebooks are disabled during fill
    to prevent interference with notebook execution. Use --allow-export
    to enable them.

    Respects skip directives:
    - #|eval: false - Skip a single cell
    - #|skip_evals - Skip all following cells
    - #|skip_evals_stop - Resume execution
    """
    from nblite.cli._helpers import get_config_path

    config_path = get_config_path(ctx)
    exit_code = _run_fill(
        notebooks=notebooks,
        code_locations=code_locations,
        timeout=timeout,
        n_workers=n_workers,
        fill_unchanged=fill_unchanged,
        remove_outputs_first=remove_outputs_first,
        clean=clean,
        save_hash=save_hash,
        exclude_dunders=not include_dunders,
        exclude_hidden=not include_hidden,
        dry_run=dry_run,
        silent=silent,
        allow_export=allow_export,
        config_path=config_path,
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command()
def test(
    ctx: typer.Context,
    notebooks: Annotated[
        list[Path] | None,
        typer.Argument(help="Specific notebooks to test (all ipynb if omitted)"),
    ] = None,
    code_locations: Annotated[
        list[str] | None,
        typer.Option("--code-location", "-c", help="Code locations to test"),
    ] = None,
    timeout: Annotated[
        int | None,
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
    allow_export: Annotated[
        bool,
        typer.Option("--allow-export", help="Allow nbl_export() during test (disabled by default)"),
    ] = False,
) -> None:
    """Test that notebooks execute without errors (dry run).

    This is an alias for `nbl fill --dry-run`. It executes all cells
    but does not save the results, making it useful for CI/CD pipelines
    to verify notebooks run correctly.

    By default, nbl_export() calls in notebooks are disabled during test
    to prevent interference with notebook execution. Use --allow-export
    to enable them.
    """
    from nblite.cli._helpers import get_config_path

    config_path = get_config_path(ctx)
    exit_code = _run_fill(
        notebooks=notebooks,
        code_locations=code_locations,
        timeout=timeout,
        n_workers=n_workers,
        fill_unchanged=fill_unchanged,
        remove_outputs_first=False,
        clean=True,  # Doesn't matter for dry_run but keep default
        save_hash=True,  # Doesn't matter for dry_run but keep default
        exclude_dunders=not include_dunders,
        exclude_hidden=not include_hidden,
        dry_run=True,  # Always dry run for test
        silent=silent,
        allow_export=allow_export,
        config_path=config_path,
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)

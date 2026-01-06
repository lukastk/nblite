"""Documentation commands for nblite CLI."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

import typer

from nblite.cli._helpers import console, get_project
from nblite.cli.app import app


@app.command(name="render-docs")
def render_docs_cmd(
    ctx: typer.Context,
    output_folder: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output folder (default: _docs)"),
    ] = None,
    generator: Annotated[
        str | None,
        typer.Option(
            "--generator", "-g", help="Documentation generator (mkdocs, jupyterbook, quarto)"
        ),
    ] = None,
    docs_cl: Annotated[
        str | None,
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
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@app.command(name="preview-docs")
def preview_docs_cmd(
    ctx: typer.Context,
    generator: Annotated[
        str | None,
        typer.Option(
            "--generator", "-g", help="Documentation generator (mkdocs, jupyterbook, quarto)"
        ),
    ] = None,
    docs_cl: Annotated[
        str | None,
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
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Preview stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

"""Templates command for nblite CLI."""

from __future__ import annotations

import json
import urllib.request
from typing import Annotated

import typer

from nblite.cli._helpers import console
from nblite.cli.app import app

__all__ = ["install_default_templates"]


def _fetch_github_directory_contents(api_url: str) -> list[dict]:
    """
    Fetch directory contents from GitHub API.

    Args:
        api_url: GitHub API URL for directory contents

    Returns:
        List of file info dictionaries from GitHub API

    Raises:
        RuntimeError: If the API request fails
    """
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "nblite",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch from GitHub API: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response from GitHub API: {e}") from e


def _download_file(url: str) -> bytes:
    """
    Download a file from a URL.

    Args:
        url: URL to download from

    Returns:
        File contents as bytes

    Raises:
        RuntimeError: If the download fails
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "nblite"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e


@app.command(name="install-default-templates")
def install_default_templates(
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            "-o",
            help="Overwrite existing templates",
        ),
    ] = False,
) -> None:
    """Download and install default templates from GitHub.

    Downloads templates from https://github.com/lukastk/nblite/tree/main/notebook-templates
    and installs them to ~/.config/nblite/templates.

    These templates are available globally and can be used with `nbl new --template <name>`.
    Project-specific templates (in the project's templates folder) take precedence over
    global templates with the same name.

    Example:
        nbl install-default-templates
        nbl install-default-templates --overwrite
    """
    from nblite.templates import (
        GITHUB_RAW_BASE_URL,
        GITHUB_TEMPLATES_API_URL,
        get_global_templates_dir,
    )

    templates_dir = get_global_templates_dir()

    console.print(f"[blue]Installing default templates to {templates_dir}[/blue]")

    # Create the directory if it doesn't exist
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Fetch the list of templates from GitHub
    try:
        contents = _fetch_github_directory_contents(GITHUB_TEMPLATES_API_URL)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

    # Filter for files only
    files = [item for item in contents if item.get("type") == "file"]

    if not files:
        console.print("[yellow]No templates found in the repository.[/yellow]")
        return

    installed_count = 0
    skipped_count = 0

    for file_info in files:
        filename = file_info["name"]
        dest_path = templates_dir / filename

        # Check if file exists
        if dest_path.exists() and not overwrite:
            console.print(f"  [yellow]Skipping {filename} (already exists)[/yellow]")
            skipped_count += 1
            continue

        # Download the file
        download_url = f"{GITHUB_RAW_BASE_URL}/{filename}"
        try:
            content = _download_file(download_url)
            dest_path.write_bytes(content)
            action = "Updated" if dest_path.exists() else "Installed"
            console.print(f"  [green]{action} {filename}[/green]")
            installed_count += 1
        except RuntimeError as e:
            console.print(f"  [red]Failed to download {filename}: {e}[/red]")

    # Summary
    console.print()
    if installed_count > 0:
        console.print(f"[green]Successfully installed {installed_count} template(s).[/green]")
    if skipped_count > 0:
        console.print(
            f"[yellow]Skipped {skipped_count} existing template(s). "
            f"Use --overwrite to replace them.[/yellow]"
        )

    if installed_count == 0 and skipped_count > 0:
        console.print("[blue]All templates already installed.[/blue]")

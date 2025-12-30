"""
MkDocs documentation generator.

Generates documentation using MkDocs (https://www.mkdocs.org/).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from nblite.docs.generator import DocsGenerator

if TYPE_CHECKING:
    from nblite.core.project import NbliteProject

__all__ = ["MkDocsGenerator"]


class MkDocsGenerator(DocsGenerator):
    """
    Documentation generator using MkDocs.

    Creates mkdocs.yml configuration and copies notebooks
    to the docs directory for building.
    """

    def prepare(self, project: NbliteProject, output_dir: Path) -> None:
        """
        Prepare MkDocs source files.

        Creates:
        - mkdocs.yml: MkDocs configuration
        - docs/: Directory containing notebooks

        Args:
            project: The nblite project to document.
            output_dir: Directory to write documentation source.
        """
        from nblite.docs.process import process_notebook_for_docs

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create docs subdirectory for content
        docs_dir = output_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Get docs code location
        docs_cl = project.config.docs_cl or project.config.docs.code_location
        if docs_cl and docs_cl in project.code_locations:
            docs_location = project.get_code_location(docs_cl)
            notebooks = docs_location.get_notebooks()
            cl_path = docs_location.path
            cl_format = docs_location.format.value
        else:
            # Fall back to all notebooks
            notebooks = project.get_notebooks()
            cl_path = project.root_path
            cl_format = "ipynb"

        # Process and copy notebooks to docs directory
        for nb in notebooks:
            if nb.source_path is None:
                continue

            try:
                rel_path = nb.source_path.relative_to(cl_path)
            except ValueError:
                rel_path = Path(nb.source_path.name)

            dest = docs_dir / rel_path.with_suffix(".ipynb")
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Process notebook for docs (inject API docs, remove hidden cells)
            process_notebook_for_docs(nb.source_path, dest, cl_format)

        # Copy markdown files
        if docs_cl and docs_cl in project.code_locations:
            for md_file in cl_path.glob("**/*.md"):
                rel_path = md_file.relative_to(cl_path)
                excluded = False
                for pattern in project.config.docs.exclude_patterns:
                    if any(part.startswith(pattern.rstrip("*")) for part in rel_path.parts):
                        excluded = True
                        break
                if not excluded:
                    dest = docs_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(md_file, dest)

        # Generate mkdocs.yml
        config = self._generate_config(project, notebooks)
        config_path = output_dir / "mkdocs.yml"
        config_path.write_text(yaml.dump(config, default_flow_style=False))

    def build(self, output_dir: Path, final_dir: Path) -> None:
        """
        Build MkDocs documentation.

        Runs `mkdocs build` command.

        Args:
            output_dir: Directory containing documentation source.
            final_dir: Directory to write built documentation.
        """
        subprocess.run(
            [
                "mkdocs",
                "build",
                "--config-file",
                str(output_dir / "mkdocs.yml"),
                "--site-dir",
                str(final_dir),
            ],
            check=True,
        )

    def preview(self, output_dir: Path) -> None:
        """
        Start MkDocs preview server.

        Runs `mkdocs serve` command.

        Args:
            output_dir: Directory containing documentation source.
        """
        subprocess.run(
            ["mkdocs", "serve", "--config-file", str(output_dir / "mkdocs.yml")],
            check=True,
        )

    def _generate_config(self, project: NbliteProject, notebooks: list[Any]) -> dict[str, Any]:
        """Generate MkDocs mkdocs.yml content."""
        title = project.config.docs.title or project.root_path.name

        # Build nav structure
        nav = self._generate_nav(notebooks)

        config: dict[str, Any] = {
            "site_name": title,
            "theme": {
                "name": "material",
            },
            "plugins": [
                "search",
                {"mkdocs-jupyter": {"include_source": True}},
            ],
            "nav": nav,
        }

        return config

    def _generate_nav(self, notebooks: list[Any]) -> list[dict[str, str]]:
        """Generate MkDocs nav structure."""
        nav: list[dict[str, str]] = []

        # Find index notebook
        index_nb = None
        other_nbs = []

        for nb in notebooks:
            if nb.source_path is None:
                continue
            name = nb.source_path.stem
            if name in ("index", "00_index", "00_intro"):
                index_nb = nb
            else:
                other_nbs.append(nb)

        # Add index first
        if index_nb and index_nb.source_path:
            nav.append({"Home": index_nb.source_path.name})

        # Add other notebooks
        for nb in sorted(other_nbs, key=lambda n: n.source_path.name if n.source_path else ""):
            if nb.source_path is None:
                continue
            # Use stem as title, replace underscores with spaces
            title = nb.source_path.stem.replace("_", " ").replace("-", " ").title()
            nav.append({title: nb.source_path.name})

        return nav

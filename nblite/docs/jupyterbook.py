"""
Jupyter Book documentation generator.

Generates documentation using Jupyter Book (https://jupyterbook.org/).
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

__all__ = ["JupyterBookGenerator"]


class JupyterBookGenerator(DocsGenerator):
    """
    Documentation generator using Jupyter Book.

    Creates _toc.yml and _config.yml files, copies notebooks,
    and can build HTML documentation.
    """

    def prepare(self, project: NbliteProject, output_dir: Path) -> None:
        """
        Prepare Jupyter Book source files.

        Creates:
        - _config.yml: Jupyter Book configuration
        - _toc.yml: Table of contents
        - Copies notebooks from docs code location

        Args:
            project: The nblite project to document.
            output_dir: Directory to write documentation source.
        """
        from nblite.docs.process import process_notebook_for_docs

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

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

        # Process and copy notebooks to output directory
        for nb in notebooks:
            if nb.source_path is None:
                continue

            try:
                rel_path = nb.source_path.relative_to(cl_path)
            except ValueError:
                rel_path = Path(nb.source_path.name)

            dest = output_dir / rel_path.with_suffix(".ipynb")
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
                    dest = output_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(md_file, dest)

        # Generate _config.yml
        config = self._generate_config(project)
        config_path = output_dir / "_config.yml"
        config_path.write_text(yaml.dump(config, default_flow_style=False))

        # Generate _toc.yml
        toc = self._generate_toc(project, notebooks)
        toc_path = output_dir / "_toc.yml"
        toc_path.write_text(yaml.dump(toc, default_flow_style=False))

    def build(self, output_dir: Path, final_dir: Path) -> None:
        """
        Build Jupyter Book documentation.

        Runs `jupyter-book build` command.

        Args:
            output_dir: Directory containing documentation source.
            final_dir: Directory to write built documentation.
        """
        subprocess.run(
            ["jupyter-book", "build", str(output_dir), "--path-output", str(final_dir)],
            check=True,
        )

    def preview(self, output_dir: Path) -> None:
        """
        Start a preview server for Jupyter Book.

        Note: Jupyter Book doesn't have a built-in preview server.
        This uses Python's http.server on the built _build/html directory.

        Args:
            output_dir: Directory containing built documentation.
        """
        html_dir = output_dir / "_build" / "html"
        if not html_dir.exists():
            raise RuntimeError(f"Built documentation not found at {html_dir}. Run build first.")

        subprocess.run(
            ["python", "-m", "http.server", "--directory", str(html_dir)],
            check=True,
        )

    def _generate_config(self, project: NbliteProject) -> dict[str, Any]:
        """Generate Jupyter Book _config.yml content."""
        title = project.config.docs.title or project.root_path.name
        author = project.config.docs.author or ""

        config: dict[str, Any] = {
            "title": title,
            "author": author,
            "execute": {
                "execute_notebooks": "off",
            },
            "sphinx": {
                "config": {
                    "html_theme": "sphinx_book_theme",
                },
            },
        }

        return config

    def _generate_toc(self, project: NbliteProject, notebooks: list[Any]) -> dict[str, Any]:
        """Generate Jupyter Book _toc.yml content."""
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

        # Build TOC structure
        toc: dict[str, Any] = {
            "format": "jb-book",
            "root": "index"
            if index_nb
            else other_nbs[0].source_path.stem
            if other_nbs
            else "index",
            "chapters": [],
        }

        for nb in other_nbs:
            if nb.source_path is None:
                continue
            # Skip if this is the root
            if index_nb is None and nb == other_nbs[0]:
                continue
            stem = nb.source_path.stem
            toc["chapters"].append({"file": stem})

        return toc

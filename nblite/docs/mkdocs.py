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
        notebook_paths: list[Path] = []
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
            notebook_paths.append(dest.relative_to(docs_dir))

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
        config = self._generate_config(project, notebook_paths)
        config_path = output_dir / "mkdocs.yml"
        config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

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

    def _generate_config(
        self, project: NbliteProject, notebook_paths: list[Path]
    ) -> dict[str, Any]:
        """Generate MkDocs mkdocs.yml content."""
        title = project.config.docs.title or project.root_path.name

        # An explicit override replaces automatic navigation, including an empty list.
        nav = (
            project.config.docs.nav
            if project.config.docs.nav is not None
            else self._generate_nav(notebook_paths)
        )

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

    def _generate_nav(self, notebook_paths: list[Path]) -> list[dict[str, Any]]:
        """Generate a folder tree using the paths of the prepared notebooks."""
        tree: dict[str, Any] = {}
        for path in notebook_paths:
            folder = tree
            for part in path.parts[:-1]:
                folder = folder.setdefault(part, {})
            folder[path.name] = path

        def folder_nav(folder: dict[str, Any]) -> list[dict[str, Any]]:
            def sort_key(name: str) -> tuple[bool, str]:
                value = folder[name]
                is_index = isinstance(value, Path) and value.stem in (
                    "index",
                    "00_index",
                    "00_intro",
                )
                return (not is_index, name)

            nav: list[dict[str, Any]] = []
            for name in sorted(folder, key=sort_key):
                value = folder[name]
                if isinstance(value, dict):
                    title = name.replace("_", " ").replace("-", " ").title()
                    nav.append({title: folder_nav(value)})
                else:
                    title = (
                        "Home"
                        if value.stem in ("index", "00_index", "00_intro")
                        else value.stem.replace("_", " ").replace("-", " ").title()
                    )
                    nav.append({title: value.as_posix()})
            return nav

        return folder_nav(tree)

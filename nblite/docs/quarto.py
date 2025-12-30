"""
Quarto documentation generator.

Generates documentation using Quarto (https://quarto.org/).
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

__all__ = ["QuartoGenerator"]


class QuartoGenerator(DocsGenerator):
    """
    Documentation generator using Quarto.

    Creates _quarto.yml configuration and copies notebooks
    for building with Quarto.

    Requires Quarto CLI to be installed (https://quarto.org/docs/get-started/).
    """

    def prepare(self, project: NbliteProject, output_dir: Path) -> None:
        """
        Prepare Quarto source files.

        Creates:
        - _quarto.yml: Quarto configuration
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

        # Process and copy notebooks
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

        # Copy markdown and qmd files
        if docs_cl and docs_cl in project.code_locations:
            for md_file in list(cl_path.glob("**/*.md")) + list(cl_path.glob("**/*.qmd")):
                rel_path = md_file.relative_to(cl_path)
                # Check exclude patterns
                excluded = False
                for pattern in project.config.docs.exclude_patterns:
                    if any(part.startswith(pattern.rstrip("*")) for part in rel_path.parts):
                        excluded = True
                        break
                if not excluded:
                    dest = output_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(md_file, dest)

        # Generate _quarto.yml
        config = self._generate_config(project, output_dir)
        config_path = output_dir / "_quarto.yml"
        config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

    def build(self, output_dir: Path, final_dir: Path) -> None:
        """
        Build Quarto documentation.

        Runs `quarto render` command.

        Args:
            output_dir: Directory containing documentation source.
            final_dir: Directory to write built documentation.
        """
        result = subprocess.run(
            ["quarto", "render", "--output-dir", str(final_dir.resolve())],
            cwd=output_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Quarto build failed: {result.stderr}")

    def preview(self, output_dir: Path) -> None:
        """
        Start Quarto preview server.

        Runs `quarto preview` command.

        Args:
            output_dir: Directory containing documentation source.
        """
        subprocess.run(["quarto", "preview"], cwd=output_dir, check=True)

    def _build_sidebar_structure(self, output_dir: Path) -> list[Any]:
        """Build sidebar structure for Quarto."""

        def process_subfolder(folder_path: Path, rel_base: Path) -> dict[str, Any]:
            contents: dict[str, Any] = {}
            contents["section"] = folder_path.name
            rel_folder_path = folder_path.relative_to(rel_base)

            sub_contents = []
            for subfolder_path in sorted(folder_path.glob("*")):
                if not subfolder_path.is_dir():
                    continue
                if any(
                    p.startswith("__") or p.startswith(".")
                    for p in subfolder_path.relative_to(rel_base).parts
                ):
                    continue
                sub_contents.append(process_subfolder(subfolder_path, rel_base))

            if len(sub_contents) > 0:
                contents["contents"] = [{"auto": f"{rel_folder_path}/*"}, *sub_contents]
            else:
                contents["contents"] = f"{rel_folder_path}/*"

            return contents

        contents: list[Any] = [{"auto": "/*"}]
        for subfolder_path in sorted(output_dir.glob("*")):
            if not subfolder_path.is_dir():
                continue
            if subfolder_path.name.startswith(("__", ".", "_")):
                continue
            contents.append(process_subfolder(subfolder_path, output_dir))

        return contents

    def _generate_config(self, project: NbliteProject, output_dir: Path) -> dict[str, Any]:
        """Generate Quarto _quarto.yml content."""
        title = project.config.docs_title or project.config.docs.title or project.root_path.name
        sidebar_contents = self._build_sidebar_structure(output_dir)

        config: dict[str, Any] = {
            "project": {
                "type": "website",
            },
            "website": {
                "title": title,
                "sidebar": {
                    "contents": sidebar_contents,
                },
            },
            "format": {
                "html": {
                    "theme": "cosmo",
                    "toc": True,
                },
            },
        }

        if project.config.docs.execute_notebooks:
            config["execute"] = {"enabled": True}

        return config

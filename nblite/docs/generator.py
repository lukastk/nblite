"""
Documentation generator protocol and factory.

Defines the interface for documentation generators and provides
a factory function to get the appropriate generator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nblite.core.project import NbliteProject

__all__ = ["DocsGenerator", "get_generator"]


class DocsGenerator(ABC):
    """
    Abstract base class for documentation generators.

    Subclasses implement specific documentation systems like
    Jupyter Book or MkDocs.
    """

    @abstractmethod
    def prepare(self, project: NbliteProject, output_dir: Path) -> None:
        """
        Prepare documentation source files.

        Creates configuration files and copies/links notebooks
        to the output directory.

        Args:
            project: The nblite project to document.
            output_dir: Directory to write documentation source.
        """
        ...

    @abstractmethod
    def build(self, output_dir: Path, final_dir: Path) -> None:
        """
        Build the documentation.

        Args:
            output_dir: Directory containing documentation source.
            final_dir: Directory to write built documentation.
        """
        ...

    @abstractmethod
    def preview(self, output_dir: Path) -> None:
        """
        Start a preview server for the documentation.

        Args:
            output_dir: Directory containing documentation source.
        """
        ...


def get_generator(generator_name: str) -> DocsGenerator:
    """
    Get a documentation generator by name.

    Args:
        generator_name: Name of the generator ("mkdocs", "jupyterbook", or "quarto").

    Returns:
        A DocsGenerator instance.

    Raises:
        ValueError: If the generator name is not recognized.

    Example:
        >>> gen = get_generator("mkdocs")
        >>> gen.prepare(project, Path("_docs"))
    """
    from nblite.docs.jupyterbook import JupyterBookGenerator
    from nblite.docs.mkdocs import MkDocsGenerator
    from nblite.docs.quarto import QuartoGenerator

    generators: dict[str, type[DocsGenerator]] = {
        "jupyterbook": JupyterBookGenerator,
        "jupyter-book": JupyterBookGenerator,
        "mkdocs": MkDocsGenerator,
        "quarto": QuartoGenerator,
    }

    if generator_name not in generators:
        available = ", ".join(sorted(set(generators.keys())))
        raise ValueError(
            f"Unknown documentation generator: {generator_name}. Available: {available}"
        )

    return generators[generator_name]()

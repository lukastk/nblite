"""
Tests for documentation generation (Milestone 11).
"""

import json
from pathlib import Path

import pytest

from nblite.core.project import NbliteProject
from nblite.docs.generator import DocsGenerator, get_generator
from nblite.docs.jupyterbook import JupyterBookGenerator
from nblite.docs.mkdocs import MkDocsGenerator
from nblite.docs.readme import generate_readme


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a sample project for testing."""
    # Create directories
    (tmp_path / "nbs").mkdir()
    (tmp_path / "mypackage").mkdir()

    # Create index notebook
    index_content = {
        "cells": [
            {"cell_type": "markdown", "source": "# My Package\n\nThis is my package.", "metadata": {}},
            {"cell_type": "code", "source": "print('hello')", "metadata": {}, "outputs": [], "execution_count": None},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (tmp_path / "nbs" / "index.ipynb").write_text(json.dumps(index_content))

    # Create another notebook
    nb_content = {
        "cells": [
            {"cell_type": "code", "source": "#|default_exp utils\n#|export\ndef foo(): pass", "metadata": {}, "outputs": [], "execution_count": None}
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (tmp_path / "nbs" / "utils.ipynb").write_text(json.dumps(nb_content))

    # Create config
    config_content = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mypackage"
format = "module"

[docs]
code_location = "nbs"
"""
    (tmp_path / "nblite.toml").write_text(config_content)

    return tmp_path


class TestDocsGenerator:
    def test_get_jupyterbook_generator(self) -> None:
        """Test getting Jupyter Book generator."""
        gen = get_generator("jupyterbook")
        assert isinstance(gen, JupyterBookGenerator)

    def test_get_jupyterbook_generator_with_hyphen(self) -> None:
        """Test getting Jupyter Book generator with hyphen."""
        gen = get_generator("jupyter-book")
        assert isinstance(gen, JupyterBookGenerator)

    def test_get_mkdocs_generator(self) -> None:
        """Test getting MkDocs generator."""
        gen = get_generator("mkdocs")
        assert isinstance(gen, MkDocsGenerator)

    def test_unknown_generator_raises(self) -> None:
        """Test unknown generator raises error."""
        with pytest.raises(ValueError, match="Unknown documentation generator"):
            get_generator("unknown")

    def test_generators_are_docs_generator(self) -> None:
        """Test all generators are DocsGenerator subclasses."""
        assert issubclass(JupyterBookGenerator, DocsGenerator)
        assert issubclass(MkDocsGenerator, DocsGenerator)


class TestJupyterBookGenerator:
    def test_prepare_creates_toc(self, sample_project: Path) -> None:
        """Test prepare creates _toc.yml."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "_toc.yml").exists()

    def test_prepare_creates_config(self, sample_project: Path) -> None:
        """Test prepare creates _config.yml."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "_config.yml").exists()

    def test_prepare_copies_notebooks(self, sample_project: Path) -> None:
        """Test prepare copies notebooks to output dir."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "index.ipynb").exists()
        assert (output_dir / "utils.ipynb").exists()

    def test_config_has_required_fields(self, sample_project: Path) -> None:
        """Test generated config has required fields."""
        import yaml

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        config = yaml.safe_load((output_dir / "_config.yml").read_text())
        assert "title" in config
        assert "execute" in config

    def test_toc_has_index_as_root(self, sample_project: Path) -> None:
        """Test TOC has index as root."""
        import yaml

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        toc = yaml.safe_load((output_dir / "_toc.yml").read_text())
        assert toc["root"] == "index"


class TestMkDocsGenerator:
    def test_prepare_creates_config(self, sample_project: Path) -> None:
        """Test prepare creates mkdocs.yml."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = MkDocsGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "mkdocs.yml").exists()

    def test_prepare_creates_docs_dir(self, sample_project: Path) -> None:
        """Test prepare creates docs subdirectory."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = MkDocsGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "docs").is_dir()

    def test_prepare_copies_notebooks(self, sample_project: Path) -> None:
        """Test prepare copies notebooks to docs dir."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = MkDocsGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "docs" / "index.ipynb").exists()
        assert (output_dir / "docs" / "utils.ipynb").exists()

    def test_config_has_required_fields(self, sample_project: Path) -> None:
        """Test generated config has required fields."""
        import yaml

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = MkDocsGenerator()
        gen.prepare(project, output_dir)

        config = yaml.safe_load((output_dir / "mkdocs.yml").read_text())
        assert "site_name" in config
        assert "theme" in config
        assert "nav" in config


class TestReadmeGeneration:
    def test_generate_readme(self, sample_project: Path) -> None:
        """Test generating README from index notebook."""
        project = NbliteProject.from_path(sample_project)
        readme_path = sample_project / "README.md"

        generate_readme(project, readme_path)

        assert readme_path.exists()
        content = readme_path.read_text()
        assert "My Package" in content

    def test_readme_contains_markdown_content(self, sample_project: Path) -> None:
        """Test README contains markdown from notebook."""
        project = NbliteProject.from_path(sample_project)
        readme_path = sample_project / "README.md"

        generate_readme(project, readme_path)

        content = readme_path.read_text()
        assert "This is my package." in content

    def test_readme_no_index_raises(self, tmp_path: Path) -> None:
        """Test README generation fails without index notebook."""
        # Create project without index
        (tmp_path / "nbs").mkdir()
        (tmp_path / "nblite.toml").write_text('export_pipeline = ""\n\n[cl.nbs]\npath = "nbs"\nformat = "ipynb"')

        project = NbliteProject.from_path(tmp_path)

        with pytest.raises(FileNotFoundError, match="No index notebook found"):
            generate_readme(project, tmp_path / "README.md")

    def test_generate_readme_with_specific_notebook(self, sample_project: Path) -> None:
        """Test generating README from specific notebook."""
        # Create a custom index notebook
        custom_content = {
            "cells": [
                {"cell_type": "markdown", "source": "# Custom Index", "metadata": {}},
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        (sample_project / "nbs" / "custom_readme.ipynb").write_text(json.dumps(custom_content))

        project = NbliteProject.from_path(sample_project)
        readme_path = sample_project / "README.md"

        generate_readme(project, readme_path, index_notebook="custom_readme")

        content = readme_path.read_text()
        assert "Custom Index" in content

    def test_readme_code_as_code_blocks(self, sample_project: Path) -> None:
        """Test code cells are formatted as code blocks."""
        project = NbliteProject.from_path(sample_project)
        readme_path = sample_project / "README.md"

        generate_readme(project, readme_path)

        content = readme_path.read_text()
        assert "```python" in content
        assert "print('hello')" in content
        assert "```" in content

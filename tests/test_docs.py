"""
Tests for documentation generation (Milestone 11).
"""

import json
from pathlib import Path

import pytest

from nblite.core.project import NbliteProject
from nblite.docs import (
    extract_class_meta,
    extract_function_meta,
    extract_top_level_definitions,
    process_notebook_for_docs,
    render_cell_doc,
    render_class_doc,
    render_function_doc,
)
from nblite.docs.generator import DocsGenerator, get_generator
from nblite.docs.jupyterbook import JupyterBookGenerator
from nblite.docs.mkdocs import MkDocsGenerator
from nblite.docs.quarto import QuartoGenerator
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
            {
                "cell_type": "markdown",
                "source": "# My Package\n\nThis is my package.",
                "metadata": {},
            },
            {
                "cell_type": "code",
                "source": "print('hello')",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (tmp_path / "nbs" / "index.ipynb").write_text(json.dumps(index_content))

    # Create another notebook
    nb_content = {
        "cells": [
            {
                "cell_type": "code",
                "source": "#|default_exp utils\n#|export\ndef foo(): pass",
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
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
        (tmp_path / "nblite.toml").write_text(
            'export_pipeline = ""\n\n[cl.nbs]\npath = "nbs"\nformat = "ipynb"'
        )

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
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
            },
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


class TestQuartoGenerator:
    def test_get_quarto_generator(self) -> None:
        """Test getting Quarto generator."""
        gen = get_generator("quarto")
        assert isinstance(gen, QuartoGenerator)

    def test_quarto_is_docs_generator(self) -> None:
        """Test Quarto generator is DocsGenerator subclass."""
        assert issubclass(QuartoGenerator, DocsGenerator)

    def test_prepare_creates_quarto_yml(self, sample_project: Path) -> None:
        """Test prepare creates _quarto.yml."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = QuartoGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "_quarto.yml").exists()

    def test_prepare_copies_notebooks(self, sample_project: Path) -> None:
        """Test prepare copies notebooks to output dir."""
        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = QuartoGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "index.ipynb").exists() or (output_dir / "index.qmd").exists()

    def test_config_has_required_fields(self, sample_project: Path) -> None:
        """Test generated config has required fields."""
        import yaml

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = QuartoGenerator()
        gen.prepare(project, output_dir)

        config = yaml.safe_load((output_dir / "_quarto.yml").read_text())
        assert "project" in config
        assert "website" in config


class TestCellDocs:
    def test_extract_function_meta(self) -> None:
        """Test extracting function metadata from source."""
        source = '''def greet(name: str, age: int = 0) -> str:
    """Say hello to someone.

    Args:
        name: The person's name.
        age: The person's age.

    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"
'''
        meta = extract_function_meta(source)
        assert meta is not None
        assert meta["name"] == "greet"
        assert "name" in meta["args"]
        assert meta["args"]["name"] == "str"
        assert "age" in meta["args"]
        assert meta["return_annotation"] == "str"
        assert "Say hello" in (meta["docstring"] or "")

    def test_extract_function_meta_no_docstring(self) -> None:
        """Test extracting function metadata without docstring."""
        source = """def add(a: int, b: int) -> int:
    return a + b
"""
        meta = extract_function_meta(source)
        assert meta is not None
        assert meta["name"] == "add"
        assert meta["docstring"] is None

    def test_extract_function_meta_raises_for_multiple(self) -> None:
        """Test extracting metadata raises error for multiple functions."""
        source = """def foo(): pass
def bar(): pass"""
        with pytest.raises(ValueError, match="Expected exactly one function"):
            extract_function_meta(source)

    def test_extract_class_meta(self) -> None:
        """Test extracting class metadata from source."""
        source = '''class Person:
    """Represents a person.

    Attributes:
        name: The person's name.
    """

    def __init__(self, name: str):
        """Initialize a Person.

        Args:
            name: The person's name.
        """
        self.name = name

    def greet(self) -> str:
        """Return a greeting."""
        return f"Hello, {self.name}"
'''
        meta = extract_class_meta(source)
        assert meta is not None
        assert meta["name"] == "Person"
        assert "Represents a person" in (meta["docstring"] or "")
        assert len(meta["methods"]) >= 1

    def test_extract_class_meta_empty_for_no_class(self) -> None:
        """Test extracting metadata returns empty dict for no class."""
        source = "def foo(): pass"
        meta = extract_class_meta(source)
        assert meta == {}

    def test_extract_top_level_definitions(self) -> None:
        """Test extracting all top-level definitions from source."""
        source = """def foo(): pass

class Bar:
    pass

def baz(): pass
"""
        defs = extract_top_level_definitions(source)
        assert len(defs) == 3
        types = [d["type"] for d in defs]
        assert types.count("function") == 2
        assert types.count("class") == 1

    def test_render_function_doc(self) -> None:
        """Test rendering function documentation to markdown."""
        source = '''def greet(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        meta = extract_function_meta(source)
        assert meta is not None
        doc = render_function_doc(meta)
        assert "greet" in doc
        assert "name" in doc
        assert "str" in doc

    def test_render_class_doc(self) -> None:
        """Test rendering class documentation to markdown."""
        source = '''class Person:
    """A person class."""
    def greet(self): pass
'''
        meta = extract_class_meta(source)
        assert meta is not None
        doc = render_class_doc(meta)
        assert "Person" in doc

    def test_render_cell_doc(self) -> None:
        """Test rendering documentation for all definitions in a cell."""
        source = '''def foo():
    """Function foo."""
    pass

class Bar:
    """Class Bar."""
    pass
'''
        doc = render_cell_doc(source)
        assert "foo" in doc
        assert "Bar" in doc


class TestProcessNotebookForDocs:
    def test_process_notebook_basic(self, tmp_path: Path) -> None:
        """Test basic notebook processing."""
        source_nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        source_path = tmp_path / "source.ipynb"
        source_path.write_text(json.dumps(source_nb))

        dest_path = tmp_path / "dest.ipynb"
        process_notebook_for_docs(source_path, dest_path)

        assert dest_path.exists()
        result = json.loads(dest_path.read_text())
        assert len(result["cells"]) >= 1

    def test_process_removes_hidden_cells(self, tmp_path: Path) -> None:
        """Test that hidden cells are removed."""
        source_nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|hide\nsecret_code()",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
                {
                    "cell_type": "code",
                    "source": "visible_code()",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        source_path = tmp_path / "source.ipynb"
        source_path.write_text(json.dumps(source_nb))

        dest_path = tmp_path / "dest.ipynb"
        process_notebook_for_docs(source_path, dest_path)

        result = json.loads(dest_path.read_text())
        # Hidden cell should be removed
        sources = [c.get("source", "") for c in result["cells"]]
        source_text = "".join(s if isinstance(s, str) else "".join(s) for s in sources)
        assert "secret_code" not in source_text

    def test_process_removes_exporti_cells(self, tmp_path: Path) -> None:
        """Test that exporti cells are removed."""
        source_nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|exporti\ndef _internal(): pass",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
                {
                    "cell_type": "code",
                    "source": "public_code()",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        source_path = tmp_path / "source.ipynb"
        source_path.write_text(json.dumps(source_nb))

        dest_path = tmp_path / "dest.ipynb"
        process_notebook_for_docs(source_path, dest_path)

        result = json.loads(dest_path.read_text())
        sources = [c.get("source", "") for c in result["cells"]]
        source_text = "".join(s if isinstance(s, str) else "".join(s) for s in sources)
        assert "_internal" not in source_text


class TestDocsConfig:
    def test_docs_config_defaults(self, tmp_path: Path) -> None:
        """Test docs config default values."""
        config_content = """
export_pipeline = ""

[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nbs").mkdir()
        (tmp_path / "nblite.toml").write_text(config_content)

        project = NbliteProject.from_path(tmp_path)
        assert project.config.docs.output_folder == "_docs"
        assert project.config.docs.execute_notebooks is False

    def test_docs_generator_default(self, tmp_path: Path) -> None:
        """Test default docs generator is mkdocs."""
        config_content = """
export_pipeline = ""

[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nbs").mkdir()
        (tmp_path / "nblite.toml").write_text(config_content)

        project = NbliteProject.from_path(tmp_path)
        assert project.config.docs_generator == "mkdocs"

    def test_docs_generator_custom(self, tmp_path: Path) -> None:
        """Test custom docs generator setting."""
        config_content = """
export_pipeline = ""
docs_generator = "quarto"

[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (tmp_path / "nbs").mkdir()
        (tmp_path / "nblite.toml").write_text(config_content)

        project = NbliteProject.from_path(tmp_path)
        assert project.config.docs_generator == "quarto"

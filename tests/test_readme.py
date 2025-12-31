"""
Tests for the readme generation module.
"""

import json
from pathlib import Path

from nblite.readme import generate_readme, notebook_to_markdown


class TestNotebookToMarkdown:
    def test_convert_markdown_cell(self) -> None:
        """Test converting a markdown cell."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {"cell_type": "markdown", "source": "# Title\n\nSome text", "metadata": {}},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        assert "# Title" in md
        assert "Some text" in md

    def test_convert_code_cell(self) -> None:
        """Test converting a code cell to fenced code block."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "def foo():\n    return 42",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        assert "```python" in md
        assert "def foo():" in md
        assert "return 42" in md
        assert "```" in md

    def test_hide_directive_filters_cell(self) -> None:
        """Test that #|hide directive filters out the cell."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|hide\nsecret_code()",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "visible_code()",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        assert "secret_code" not in md
        assert "visible_code" in md

    def test_directives_stripped_from_code(self) -> None:
        """Test that directives are stripped from code output."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef exported_func():\n    pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        assert "#|export" not in md
        assert "def exported_func():" in md

    def test_include_stream_output(self) -> None:
        """Test that stream outputs are included."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "print('hello')",
                        "metadata": {},
                        "outputs": [{"output_type": "stream", "name": "stdout", "text": "hello\n"}],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        assert "hello" in md

    def test_include_execute_result(self) -> None:
        """Test that execute_result outputs are included."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "42",
                        "metadata": {},
                        "outputs": [
                            {
                                "output_type": "execute_result",
                                "data": {"text/plain": "42"},
                                "execution_count": 1,
                                "metadata": {},
                            }
                        ],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        # Output should be in a code block
        assert "42" in md

    def test_empty_code_cell_not_included(self) -> None:
        """Test that empty code cells are not included."""
        from nblite.core.notebook import Notebook

        nb = Notebook.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\n",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        md = notebook_to_markdown(nb)
        # Should not have a code block since stripped source is empty
        assert "```python" not in md or md.count("```python") == 0


class TestGenerateReadme:
    def test_generate_readme_creates_file(self, tmp_path: Path) -> None:
        """Test that generate_readme creates a file."""
        nb_content = json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": "# My Project", "metadata": {}},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "index.ipynb"
        nb_path.write_text(nb_content)

        output_path = tmp_path / "README.md"
        result = generate_readme(nb_path, output_path)

        assert output_path.exists()
        assert "# My Project" in output_path.read_text()
        assert "# My Project" in result

    def test_generate_readme_without_writing(self, tmp_path: Path) -> None:
        """Test generate_readme returns markdown without writing."""
        nb_content = json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": "# Test", "metadata": {}},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "index.ipynb"
        nb_path.write_text(nb_content)

        result = generate_readme(nb_path, output_path=None)

        assert "# Test" in result


class TestReadmeConfigOption:
    def test_config_parses_readme_nb_path(self, tmp_path: Path) -> None:
        """Test that readme_nb_path is parsed from config."""
        from nblite.config import load_config

        config_content = """
export_pipeline = ""
readme_nb_path = "nbs/index.ipynb"

[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        config_path = tmp_path / "nblite.toml"
        config_path.write_text(config_content)

        config = load_config(config_path)
        assert config.readme_nb_path == "nbs/index.ipynb"

    def test_config_readme_nb_path_defaults_to_none(self, tmp_path: Path) -> None:
        """Test that readme_nb_path defaults to None."""
        from nblite.config import load_config

        config_content = """
export_pipeline = ""

[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        config_path = tmp_path / "nblite.toml"
        config_path.write_text(config_content)

        config = load_config(config_path)
        assert config.readme_nb_path is None

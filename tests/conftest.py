"""
Shared pytest fixtures for nblite tests.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary nblite project structure."""
    # Create directories
    (tmp_path / "nbs").mkdir()
    (tmp_path / "pts").mkdir()
    (tmp_path / "mypackage").mkdir()

    # Create a basic nblite.toml
    config_content = '''
export_pipeline = """
nbs -> pts
pts -> lib
"""

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pts]
path = "pts"
format = "percent"

[cl.lib]
path = "mypackage"
format = "module"
'''
    (tmp_path / "nblite.toml").write_text(config_content)

    return tmp_path


@pytest.fixture
def sample_notebook_content() -> str:
    """Return sample notebook JSON content."""
    return json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|default_exp utils",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
                {
                    "cell_type": "code",
                    "source": "#|export\ndef foo():\n    pass",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )


@pytest.fixture
def sample_notebook(tmp_path: Path, sample_notebook_content: str) -> Path:
    """Create a sample notebook file."""
    nb_path = tmp_path / "test.ipynb"
    nb_path.write_text(sample_notebook_content)
    return nb_path


@pytest.fixture
def sample_pct_content() -> str:
    """Return sample percent-format notebook content."""
    return """# %%
#|default_exp utils

# %%
#|export
def foo():
    pass
"""


@pytest.fixture
def sample_pct_file(tmp_path: Path, sample_pct_content: str) -> Path:
    """Create a sample percent-format notebook file."""
    pct_path = tmp_path / "test.pct.py"
    pct_path.write_text(sample_pct_content)
    return pct_path

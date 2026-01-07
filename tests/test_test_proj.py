"""
Tests for the test_proj example project.

These tests verify that nblite works correctly with a real project structure.
"""

import json
from pathlib import Path

import pytest

from nblite.config.schema import CodeLocationFormat
from nblite.core.notebook import Notebook
from nblite.core.project import NbliteProject

# Path to the test project directory
TEST_PROJ_PATH = Path(__file__).parent.parent / "example_projects" / "00_basic"


class TestProjectLoading:
    """Test loading the test_proj project."""

    def test_project_exists(self) -> None:
        """Test that test_proj directory exists."""
        assert TEST_PROJ_PATH.exists()
        assert (TEST_PROJ_PATH / "nblite.toml").exists()

    def test_load_project(self) -> None:
        """Test loading the project."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)
        assert project is not None
        assert project.root_path == TEST_PROJ_PATH.resolve()

    def test_project_config(self) -> None:
        """Test project configuration is loaded correctly."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)
        config = project.config

        assert len(config.code_locations) == 3
        assert "nbs" in config.code_locations
        assert "pcts" in config.code_locations
        assert "lib" in config.code_locations

    def test_export_pipeline(self) -> None:
        """Test export pipeline configuration."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)
        config = project.config

        assert len(config.export_pipeline) == 2
        assert config.export_pipeline[0].from_key == "nbs"
        assert config.export_pipeline[0].to_key == "pcts"
        assert config.export_pipeline[1].from_key == "pcts"
        assert config.export_pipeline[1].to_key == "lib"


class TestNotebookDiscovery:
    """Test discovering notebooks in the test project."""

    def test_discover_all_notebooks(self) -> None:
        """Test that all notebooks are discovered."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)
        notebooks = project.notebooks

        # Should find: index, core, directives_demo, workflow, submodule/utils
        assert len(notebooks) >= 5

    def test_discover_notebooks_by_location(self) -> None:
        """Test discovering notebooks in specific code location."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)
        nbs_notebooks = project.get_notebooks("nbs")

        assert len(nbs_notebooks) >= 5

        # Check that expected notebooks exist
        nb_names = [nb.source_path.stem for nb in nbs_notebooks if nb.source_path]
        assert "index" in nb_names
        assert "core" in nb_names
        assert "workflow" in nb_names
        assert "directives_demo" in nb_names

    def test_submodule_notebook_discovery(self) -> None:
        """Test that notebooks in subdirectories are discovered."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)
        nbs_notebooks = project.get_notebooks("nbs")

        # Find the utils notebook in submodule
        submodule_nbs = [
            nb for nb in nbs_notebooks if nb.source_path and "submodule" in str(nb.source_path)
        ]
        assert len(submodule_nbs) == 1
        assert submodule_nbs[0].source_path.stem == "utils"


class TestNotebookParsing:
    """Test parsing notebooks from test_proj."""

    def test_parse_core_notebook(self) -> None:
        """Test parsing the core notebook."""
        nb_path = TEST_PROJ_PATH / "nbs" / "core.ipynb"
        nb = Notebook.from_file(nb_path)

        assert nb is not None
        assert len(nb.cells) > 0
        assert nb.default_exp == "core"

    def test_parse_workflow_notebook(self) -> None:
        """Test parsing the workflow (function) notebook."""
        nb_path = TEST_PROJ_PATH / "nbs" / "workflow.ipynb"
        nb = Notebook.from_file(nb_path)

        assert nb is not None
        assert nb.default_exp == "workflow"

        # Check for export_as_func directive
        has_export_as_func = any(cell.has_directive("export_as_func") for cell in nb.cells)
        assert has_export_as_func

    def test_parse_directives_notebook(self) -> None:
        """Test parsing the directives demo notebook."""
        nb_path = TEST_PROJ_PATH / "nbs" / "directives_demo.ipynb"
        nb = Notebook.from_file(nb_path)

        assert nb is not None
        assert nb.default_exp == "directives_demo"

        # Count cells with various directives
        export_cells = [c for c in nb.cells if c.has_directive("export")]
        hide_cells = [c for c in nb.cells if c.has_directive("hide")]
        eval_cells = [c for c in nb.cells if c.has_directive("eval")]

        assert len(export_cells) >= 3
        assert len(hide_cells) >= 2
        assert len(eval_cells) >= 1

    def test_submodule_notebook_default_exp(self) -> None:
        """Test that submodule notebook has correct default_exp."""
        nb_path = TEST_PROJ_PATH / "nbs" / "submodule" / "utils.ipynb"
        nb = Notebook.from_file(nb_path)

        assert nb.default_exp == "submodule.utils"


class TestExportPipeline:
    """Test the export pipeline with test_proj."""

    def test_export_creates_pct_files(self, tmp_path: Path) -> None:
        """Test that export creates percent format files."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # Check that pcts directory has files
        pcts_dir = test_copy / "pcts"
        assert pcts_dir.exists()

        pct_files = list(pcts_dir.glob("**/*.pct.py"))
        assert len(pct_files) >= 4  # core, workflow, directives_demo, index

    def test_export_creates_module_files(self, tmp_path: Path) -> None:
        """Test that export creates Python module files."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # Check that my_lib directory has exported modules
        lib_dir = test_copy / "my_lib"
        assert lib_dir.exists()

        py_files = list(lib_dir.glob("**/*.py"))
        # Should have: __init__.py, core.py, workflow.py, directives_demo.py, submodule/utils.py
        assert len(py_files) >= 4

    def test_exported_core_module_content(self, tmp_path: Path) -> None:
        """Test that exported core module has correct content."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # Check core.py content
        core_py = test_copy / "my_lib" / "core.py"
        assert core_py.exists()

        content = core_py.read_text()
        assert "def greet" in content
        assert "def add" in content
        assert "class Calculator" in content
        # Non-exported code should not be present
        assert "calc = Calculator" not in content

    def test_exported_workflow_is_function(self, tmp_path: Path) -> None:
        """Test that workflow notebook exports as a function."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # Check workflow.py content
        workflow_py = test_copy / "my_lib" / "workflow.py"
        assert workflow_py.exists()

        content = workflow_py.read_text()
        assert "def run_workflow" in content
        assert "input_path: str" in content
        assert "return result" in content

    def test_duplicate_default_exp_raises_error(self, tmp_path: Path) -> None:
        """Test that duplicate #|default_exp raises an error."""
        import json

        # Create a minimal project with two notebooks having the same default_exp
        project_dir = tmp_path / "dup_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create first notebook with default_exp = "shared"
        nb1_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp shared",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef from_nb1(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "nb1.ipynb").write_text(nb1_content)

        # Create second notebook with the SAME default_exp = "shared"
        nb2_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp shared",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef from_nb2(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "nb2.ipynb").write_text(nb2_content)

        # Try to export - should raise ValueError
        project = NbliteProject.from_path(project_dir)
        with pytest.raises(ValueError, match="Multiple notebooks have the same #|default_exp"):
            project.export()

    def test_export_to_same_module_allowed(self, tmp_path: Path) -> None:
        """Test that #|export_to to the same module from multiple notebooks is allowed."""
        import json

        # Create a minimal project with two notebooks using export_to to same module
        project_dir = tmp_path / "export_to_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create first notebook using export_to (no default_exp for 'shared')
        nb1_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export_to shared\ndef from_nb1(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "nb1.ipynb").write_text(nb1_content)

        # Create second notebook also using export_to to same module
        nb2_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export_to shared\ndef from_nb2(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "nb2.ipynb").write_text(nb2_content)

        # Export should succeed
        project = NbliteProject.from_path(project_dir)
        result = project.export()
        assert result.success

        # Both functions should be in the output
        shared_py = lib_dir / "shared.py"
        assert shared_py.exists()
        content = shared_py.read_text()
        assert "def from_nb1():" in content
        assert "def from_nb2():" in content

    def test_export_without_default_exp_raises_error(self, tmp_path: Path) -> None:
        """Test that #|export without #|default_exp raises an error."""
        import json

        # Create a minimal project with a notebook using #|export but no #|default_exp
        project_dir = tmp_path / "no_default_exp_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create notebook with #|export but NO #|default_exp
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef orphan_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "orphan.ipynb").write_text(nb_content)

        # Try to export - should raise ValueError
        project = NbliteProject.from_path(project_dir)
        with pytest.raises(ValueError, match="uses #|export or #|exporti without #|default_exp"):
            project.export()

    def test_exporti_without_default_exp_raises_error(self, tmp_path: Path) -> None:
        """Test that #|exporti without #|default_exp also raises an error."""
        import json

        # Create a minimal project
        project_dir = tmp_path / "no_default_exp_proj2"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create notebook with #|exporti but NO #|default_exp
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|exporti\ndef _private_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "orphan.ipynb").write_text(nb_content)

        # Try to export - should raise ValueError
        project = NbliteProject.from_path(project_dir)
        with pytest.raises(ValueError, match="uses #|export or #|exporti without #|default_exp"):
            project.export()

    def test_unrecognized_directive_warns(self, tmp_path: Path) -> None:
        """Test that unrecognized directives produce warnings."""
        import json

        # Create a minimal project with an unrecognized directive
        project_dir = tmp_path / "warn_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create notebook with an unrecognized directive
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp mymodule",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\n#|unknown_directive\ndef func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # Export should succeed but produce warnings
        project = NbliteProject.from_path(project_dir)
        result = project.export()
        assert result.success
        assert len(result.warnings) == 1
        assert "unknown_directive" in result.warnings[0]
        assert "nbs" in result.warnings[0]  # source path should be in warning

    def test_silence_warnings_suppresses_collection(self, tmp_path: Path) -> None:
        """Test that silence_warnings=True still collects warnings in result."""
        import json

        # Create a minimal project with an unrecognized directive
        project_dir = tmp_path / "silence_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create notebook with an unrecognized directive
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp mymodule",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\n#|fake_directive value\ndef func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # Export with silence_warnings=True
        project = NbliteProject.from_path(project_dir)
        result = project.export(silence_warnings=True)
        assert result.success
        # Warnings should still be collected (just not printed by CLI)
        assert len(result.warnings) == 1
        assert "fake_directive" in result.warnings[0]


class TestReversePipeline:
    """Test the reverse pipeline feature."""

    def test_get_reversed_pipeline_excludes_modules(self, tmp_path: Path) -> None:
        """Test that get_reversed_pipeline excludes module code locations."""
        import json

        # Create a project with nbs -> pts -> lib pipeline
        project_dir = tmp_path / "reverse_proj"
        nbs_dir = project_dir / "nbs"
        pts_dir = project_dir / "pts"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        pts_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml with multi-step pipeline
        config = """
export_pipeline = \"\"\"
nbs -> pts
pts -> lib
\"\"\"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pts]
path = "pts"
format = "percent"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test\n#|export\ndef func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(project_dir)
        reversed_pipeline = project.get_reversed_pipeline()

        # Should only include "pts -> nbs", not "lib -> pts"
        assert reversed_pipeline == "pts -> nbs"

    def test_get_reversed_pipeline_no_modules(self, tmp_path: Path) -> None:
        """Test reverse pipeline when there are no module code locations."""
        import json

        # Create a project with only notebook code locations
        project_dir = tmp_path / "reverse_proj2"
        nbs_dir = project_dir / "nbs"
        pts_dir = project_dir / "pts"
        nbs_dir.mkdir(parents=True)
        pts_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> pts"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pts]
path = "pts"
format = "percent"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(project_dir)
        reversed_pipeline = project.get_reversed_pipeline()

        assert reversed_pipeline == "pts -> nbs"

    def test_get_reversed_pipeline_only_modules(self, tmp_path: Path) -> None:
        """Test reverse pipeline when all destinations are modules."""
        import json

        # Create a project where all rules go to modules
        project_dir = tmp_path / "reverse_proj3"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test\n#|export\ndef func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(project_dir)
        reversed_pipeline = project.get_reversed_pipeline()

        # Should return None since all rules involve modules
        assert reversed_pipeline is None

    def test_reverse_export_syncs_changes(self, tmp_path: Path) -> None:
        """Test that reverse export actually syncs changes from pts to nbs."""
        import json

        # Create a project
        project_dir = tmp_path / "reverse_proj4"
        nbs_dir = project_dir / "nbs"
        pts_dir = project_dir / "pts"
        nbs_dir.mkdir(parents=True)
        pts_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> pts"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pts]
path = "pts"
format = "percent"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # First, export nbs -> pts
        project = NbliteProject.from_path(project_dir)
        project.export()

        # Verify pts file was created
        pts_file = pts_dir / "test.pct.py"
        assert pts_file.exists()
        assert "x = 1" in pts_file.read_text()

        # Now modify the pts file
        pts_file.write_text("# %%\ny = 2\n")

        # Reverse export: pts -> nbs
        reversed_pipeline = project.get_reversed_pipeline()
        assert reversed_pipeline == "pts -> nbs"
        result = project.export(pipeline=reversed_pipeline)
        assert result.success

        # Verify nbs file was updated
        nbs_file = nbs_dir / "test.ipynb"
        nb_data = json.loads(nbs_file.read_text())
        assert "y = 2" in nb_data["cells"][0]["source"]


class TestDunderFolderExport:
    """Test that notebooks in dunder folders are handled correctly."""

    def test_dunder_folder_not_exported_to_module(self, tmp_path: Path) -> None:
        """Test that notebooks in __dunder__ folders are NOT exported to modules."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        # Create a notebook inside a dunder folder
        dunder_dir = test_copy / "nbs" / "__tests__"
        dunder_dir.mkdir(parents=True)

        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test_utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef test_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        test_nb = dunder_dir / "test_utils.ipynb"
        test_nb.write_text(nb_content)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # The notebook should NOT be exported to the module location
        module_path = test_copy / "my_lib" / "test_utils.py"
        assert not module_path.exists(), (
            "Notebooks in dunder folders should not be exported to modules"
        )

    def test_dunder_folder_exported_to_notebook_format(self, tmp_path: Path) -> None:
        """Test that notebooks in __dunder__ folders ARE exported to other notebook formats."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        # Create a notebook inside a dunder folder
        dunder_dir = test_copy / "nbs" / "__tests__"
        dunder_dir.mkdir(parents=True)

        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test_utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "def test_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        test_nb = dunder_dir / "test_utils.ipynb"
        test_nb.write_text(nb_content)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # The notebook SHOULD be exported to the percent format location
        pct_path = test_copy / "pcts" / "__tests__" / "test_utils.pct.py"
        assert pct_path.exists(), (
            "Notebooks in dunder folders should still be exported to notebook formats"
        )

    def test_dunder_filename_not_exported_to_module(self, tmp_path: Path) -> None:
        """Test that notebooks with __dunder__ filenames are NOT exported to modules."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        # Create a notebook with a dunder filename
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp __private_utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef private_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        test_nb = test_copy / "nbs" / "__private.ipynb"
        test_nb.write_text(nb_content)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # The notebook should NOT be exported to the module location
        module_path = test_copy / "my_lib" / "__private_utils.py"
        assert not module_path.exists(), (
            "Notebooks with dunder filenames should not be exported to modules"
        )

    def test_nested_dunder_folder_not_exported_to_module(self, tmp_path: Path) -> None:
        """Test that notebooks in nested dunder folders are NOT exported to modules."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        # Create a notebook inside a nested dunder folder
        dunder_dir = test_copy / "nbs" / "__tests__" / "unit"
        dunder_dir.mkdir(parents=True)

        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp unit_tests",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef unit_test(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        test_nb = dunder_dir / "test_core.ipynb"
        test_nb.write_text(nb_content)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # The notebook should NOT be exported to the module location
        module_path = test_copy / "my_lib" / "unit_tests.py"
        assert not module_path.exists(), (
            "Notebooks in nested dunder folders should not be exported to modules"
        )

    def test_get_notebook_twins_excludes_module_for_dunder(self, tmp_path: Path) -> None:
        """Test that get_notebook_twins excludes module twin for dunder folder notebooks."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        # Create a notebook inside a dunder folder
        dunder_dir = test_copy / "nbs" / "__tests__"
        dunder_dir.mkdir(parents=True)

        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test_utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef test_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        test_nb = dunder_dir / "test_utils.ipynb"
        test_nb.write_text(nb_content)

        project = NbliteProject.from_path(test_copy)

        # Get twins for the dunder folder notebook
        nb = Notebook.from_file(test_nb)
        twins = project.get_notebook_twins(nb)

        # Should have twin in pcts but NOT in lib (module)
        twin_paths = [str(t) for t in twins]
        assert any("pcts" in p and "test_utils.pct.py" in p for p in twin_paths), (
            "Dunder folder notebooks should have pcts twins"
        )
        assert not any("my_lib" in p for p in twin_paths), (
            "Dunder folder notebooks should NOT have module twins"
        )


class TestNotebookTwins:
    """Test twin tracking in test_proj."""

    def test_get_notebook_twins(self, tmp_path: Path) -> None:
        """Test getting twins for a notebook."""
        import shutil

        # Copy test_proj to tmp_path
        test_copy = tmp_path / "test_proj"
        shutil.copytree(TEST_PROJ_PATH, test_copy)

        project = NbliteProject.from_path(test_copy)
        project.export()

        # Get twins for core notebook
        core_nb_path = test_copy / "nbs" / "core.ipynb"
        core_nb = Notebook.from_file(core_nb_path)
        twins = project.get_notebook_twins(core_nb)

        # Should have twins in pcts and lib
        twin_paths = [str(t) for t in twins]
        assert any("pcts" in p and "core.pct.py" in p for p in twin_paths)
        assert any("my_lib" in p and "core.py" in p for p in twin_paths)


class TestConfigOverride:
    """Test config override functionality."""

    def test_override_config_changes_value(self, tmp_path: Path) -> None:
        """Test that --override-config changes config values."""
        import json

        # Create a minimal project
        project_dir = tmp_path / "override_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml with original docs_title
        config = """
export_pipeline = "nbs -> lib"
docs_title = "Original Title"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # Load project with override
        project = NbliteProject.from_path(
            project_dir,
            config_override={"docs_title": "Overridden Title"},
        )

        assert project.config.docs_title == "Overridden Title"

    def test_add_code_location(self, tmp_path: Path) -> None:
        """Test that --add-code-location adds code locations."""
        import json

        # Create a minimal project
        project_dir = tmp_path / "add_cl_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        extra_dir = project_dir / "extra_nbs"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)
        extra_dir.mkdir(parents=True)

        # Create nblite.toml with only nbs and lib
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # Load project with extra code location
        project = NbliteProject.from_path(
            project_dir,
            add_code_locations=[{"name": "extra", "path": "extra_nbs", "format": "ipynb"}],
        )

        assert "extra" in project.config.code_locations
        assert project.config.code_locations["extra"].path == "extra_nbs"
        assert project.config.code_locations["extra"].format.value == "ipynb"

    def test_override_nested_config(self, tmp_path: Path) -> None:
        """Test overriding nested config values like [export]."""
        import json

        # Create a minimal project
        project_dir = tmp_path / "nested_override_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"

[export]
include_autogenerated_warning = true
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # Load project with override for nested config
        project = NbliteProject.from_path(
            project_dir,
            config_override={"export": {"include_autogenerated_warning": False}},
        )

        assert project.config.export.include_autogenerated_warning is False

    def test_add_code_location_missing_name_raises_error(self, tmp_path: Path) -> None:
        """Test that --add-code-location without 'name' raises error."""
        from nblite.config.loader import ConfigError

        # Create a minimal project
        project_dir = tmp_path / "bad_cl_proj"
        nbs_dir = project_dir / "nbs"
        nbs_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
[cl.nbs]
path = "nbs"
format = "ipynb"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Try to load project with code location missing 'name'
        with pytest.raises(ConfigError, match="requires 'name' field"):
            NbliteProject.from_path(
                project_dir,
                add_code_locations=[
                    {"path": "extra_nbs", "format": "ipynb"}  # Missing 'name'
                ],
            )

    def test_both_overrides_together(self, tmp_path: Path) -> None:
        """Test using both --override-config and --add-code-location together."""
        import json

        # Create a minimal project
        project_dir = tmp_path / "both_overrides_proj"
        nbs_dir = project_dir / "nbs"
        lib_dir = project_dir / "mylib"
        extra_dir = project_dir / "extra_nbs"
        nbs_dir.mkdir(parents=True)
        lib_dir.mkdir(parents=True)
        extra_dir.mkdir(parents=True)

        # Create nblite.toml
        config = """
export_pipeline = "nbs -> lib"
docs_title = "Original Title"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
"""
        (project_dir / "nblite.toml").write_text(config)

        # Create a simple notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        (nbs_dir / "test.ipynb").write_text(nb_content)

        # Load project with both overrides
        project = NbliteProject.from_path(
            project_dir,
            config_override={"docs_title": "New Title"},
            add_code_locations=[{"name": "extra", "path": "extra_nbs", "format": "ipynb"}],
        )

        assert project.config.docs_title == "New Title"
        assert "extra" in project.config.code_locations


class TestCodeLocations:
    """Test code location functionality."""

    def test_get_code_location(self) -> None:
        """Test getting specific code locations."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)

        nbs_loc = project.get_code_location("nbs")
        assert nbs_loc is not None
        assert nbs_loc.format == CodeLocationFormat.IPYNB

        pcts_loc = project.get_code_location("pcts")
        assert pcts_loc is not None
        assert pcts_loc.format == CodeLocationFormat.PERCENT

        lib_loc = project.get_code_location("lib")
        assert lib_loc is not None
        assert lib_loc.format == CodeLocationFormat.MODULE

    def test_code_location_paths(self) -> None:
        """Test code location paths are resolved correctly."""
        project = NbliteProject.from_path(TEST_PROJ_PATH)

        nbs_loc = project.get_code_location("nbs")
        assert nbs_loc.path.name == "nbs"

        lib_loc = project.get_code_location("lib")
        assert lib_loc.path.name == "my_lib"

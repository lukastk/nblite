"""
Tests for the test_proj example project.

These tests verify that nblite works correctly with a real project structure.
"""

from pathlib import Path

from nblite.config.schema import CodeLocationFormat
from nblite.core.notebook import Notebook
from nblite.core.project import NbliteProject

# Path to the test_proj directory
TEST_PROJ_PATH = Path(__file__).parent.parent / "test_proj"


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

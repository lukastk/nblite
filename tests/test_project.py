"""
Tests for the NbliteProject class (Milestone 7).
"""

import json
from pathlib import Path

import pytest

from nblite.core.project import NbliteProject, NotebookLineage


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a complete sample project."""
    # Create directories
    (tmp_path / "nbs").mkdir()
    (tmp_path / "pts").mkdir()
    (tmp_path / "mypackage").mkdir()

    # Create notebooks
    nb_content = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "#|default_exp utils\n#|export\ndef foo(): pass",
                    "metadata": {},
                    "outputs": [],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )
    (tmp_path / "nbs" / "utils.ipynb").write_text(nb_content)

    # Create config
    config_content = """
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
path = "mypackage"
format = "module"
"""
    (tmp_path / "nblite.toml").write_text(config_content)

    return tmp_path


class TestNbliteProject:
    def test_from_path(self, sample_project: Path) -> None:
        """Test loading project from path."""
        project = NbliteProject.from_path(sample_project)
        assert project.root_path == sample_project
        assert project.config is not None

    def test_from_path_with_config_file(self, sample_project: Path) -> None:
        """Test loading project by passing config file directly."""
        config_path = sample_project / "nblite.toml"
        project = NbliteProject.from_path(config_path)
        assert project.root_path == sample_project

    def test_from_path_not_found(self, tmp_path: Path) -> None:
        """Test error when no config found."""
        with pytest.raises(FileNotFoundError):
            NbliteProject.from_path(tmp_path)

    def test_find_project_root(self, sample_project: Path) -> None:
        """Test finding project root from nested path."""
        nested = sample_project / "nbs" / "subfolder"
        nested.mkdir(parents=True)

        root = NbliteProject.find_project_root(nested)
        assert root == sample_project

    def test_find_project_root_not_found(self, tmp_path: Path) -> None:
        """Test find_project_root returns None when not found."""
        root = NbliteProject.find_project_root(tmp_path)
        assert root is None

    def test_code_locations(self, sample_project: Path) -> None:
        """Test accessing code locations."""
        project = NbliteProject.from_path(sample_project)

        assert "nbs" in project.code_locations
        assert "pts" in project.code_locations
        assert "lib" in project.code_locations

    def test_get_code_location(self, sample_project: Path) -> None:
        """Test getting specific code location."""
        project = NbliteProject.from_path(sample_project)

        nbs_cl = project.get_code_location("nbs")
        assert nbs_cl.key == "nbs"
        assert nbs_cl.is_notebook is True

    def test_get_code_location_not_found(self, sample_project: Path) -> None:
        """Test error when code location not found."""
        project = NbliteProject.from_path(sample_project)

        with pytest.raises(KeyError):
            project.get_code_location("nonexistent")

    def test_get_notebooks(self, sample_project: Path) -> None:
        """Test getting notebooks from project."""
        project = NbliteProject.from_path(sample_project)

        notebooks = project.get_notebooks()
        assert len(notebooks) == 1
        assert notebooks[0].default_exp == "utils"

    def test_get_notebooks_by_location(self, sample_project: Path) -> None:
        """Test getting notebooks filtered by code location."""
        project = NbliteProject.from_path(sample_project)

        nbs_notebooks = project.get_notebooks(code_location="nbs")
        assert len(nbs_notebooks) == 1

    def test_notebooks_property(self, sample_project: Path) -> None:
        """Test notebooks property."""
        project = NbliteProject.from_path(sample_project)
        assert len(project.notebooks) == 1

    def test_py_files_property(self, sample_project: Path) -> None:
        """Test py_files property (empty before export)."""
        project = NbliteProject.from_path(sample_project)
        # No module files exist yet
        assert len(project.py_files) == 0

    def test_repr(self, sample_project: Path) -> None:
        """Test repr output."""
        project = NbliteProject.from_path(sample_project)
        repr_str = repr(project)
        assert "NbliteProject" in repr_str
        assert "nbs" in repr_str


class TestTwinTracking:
    def test_get_notebook_twins(self, sample_project: Path) -> None:
        """Test getting twin paths for a notebook."""
        project = NbliteProject.from_path(sample_project)
        notebooks = project.get_notebooks()

        twins = project.get_notebook_twins(notebooks[0])

        assert len(twins) >= 1
        # Should include the pct.py path
        assert any("pts" in str(t) for t in twins)

    def test_get_notebook_twins_no_source(self, sample_project: Path) -> None:
        """Test getting twins for notebook without source path."""
        from nblite.core.notebook import Notebook

        project = NbliteProject.from_path(sample_project)
        nb = Notebook.from_dict(
            {
                "cells": [],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )

        twins = project.get_notebook_twins(nb)
        assert twins == []


class TestLineageTracking:
    def test_get_notebook_lineage(self, sample_project: Path) -> None:
        """Test getting lineage for a notebook."""
        project = NbliteProject.from_path(sample_project)
        notebooks = project.get_notebooks()

        lineage = project.get_notebook_lineage(notebooks[0])

        assert isinstance(lineage, NotebookLineage)
        assert lineage.source == notebooks[0].source_path
        assert lineage.code_location == "nbs"

    def test_lineage_after_export(self, sample_project: Path) -> None:
        """Test getting lineage after export."""
        project = NbliteProject.from_path(sample_project)
        project.export()

        notebooks = project.get_notebooks()
        lineage = project.get_notebook_lineage(notebooks[0])

        assert "pts" in lineage.twins


class TestProjectExport:
    def test_export_all(self, sample_project: Path) -> None:
        """Test exporting all notebooks."""
        project = NbliteProject.from_path(sample_project)
        result = project.export()

        assert result.success
        assert (sample_project / "pts" / "utils.pct.py").exists()
        # Note: lib export requires pts -> lib step which needs pts notebooks to exist first

    def test_export_creates_files(self, sample_project: Path) -> None:
        """Test that export creates output files."""
        project = NbliteProject.from_path(sample_project)
        result = project.export()

        assert len(result.files_created) >= 1
        assert result.errors == []

    def test_export_specific_notebooks(self, sample_project: Path) -> None:
        """Test exporting specific notebooks."""
        project = NbliteProject.from_path(sample_project)
        nb_path = sample_project / "nbs" / "utils.ipynb"

        result = project.export(notebooks=[nb_path])
        assert result.success

    def test_export_with_custom_pipeline(self, sample_project: Path) -> None:
        """Test exporting with a custom pipeline string."""
        project = NbliteProject.from_path(sample_project)

        # Use a custom pipeline that only exports nbs -> lib (skipping pts)
        result = project.export(pipeline="nbs -> lib")

        assert result.success
        assert (sample_project / "mypackage" / "utils.py").exists()

    def test_export_with_custom_pipeline_comma_separated(self, sample_project: Path) -> None:
        """Test exporting with comma-separated pipeline rules."""
        project = NbliteProject.from_path(sample_project)

        # Both rules separated by comma
        result = project.export(pipeline="nbs -> pts, pts -> lib")

        assert result.success
        assert (sample_project / "pts" / "utils.pct.py").exists()

    def test_export_reverse_pipeline(self, sample_project: Path) -> None:
        """Test exporting with reversed pipeline (percent to ipynb)."""
        project = NbliteProject.from_path(sample_project)

        # First export to create pct.py files
        project.export(pipeline="nbs -> pts")
        assert (sample_project / "pts" / "utils.pct.py").exists()

        # Create a new ipynb output directory
        (sample_project / "nbs_out").mkdir()

        # Add nbs_out code location to config
        config_content = (sample_project / "nblite.toml").read_text()
        config_content += """
[cl.nbs_out]
path = "nbs_out"
format = "ipynb"
"""
        (sample_project / "nblite.toml").write_text(config_content)

        # Reload project and reverse export
        project = NbliteProject.from_path(sample_project)
        result = project.export(pipeline="pts -> nbs_out")

        assert result.success
        assert (sample_project / "nbs_out" / "utils.ipynb").exists()


class TestProjectClean:
    def test_clean_notebooks(self, sample_project: Path) -> None:
        """Test cleaning notebooks."""
        # Add output to notebook with proper metadata and output format
        nb_path = sample_project / "nbs" / "utils.ipynb"
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef foo(): pass",
                        "metadata": {},
                        "outputs": [{"output_type": "stream", "name": "stdout", "text": "hello"}],
                        "execution_count": 1,
                    }
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
        nb_path.write_text(nb_content)

        project = NbliteProject.from_path(sample_project)
        project.clean(remove_outputs=True)

        cleaned = json.loads(nb_path.read_text())
        assert cleaned["cells"][0]["outputs"] == []

    def test_clean_specific_notebooks(self, sample_project: Path) -> None:
        """Test cleaning specific notebooks."""
        nb_path = sample_project / "nbs" / "utils.ipynb"
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "x = 1",
                        "metadata": {},
                        "outputs": [{"output_type": "stream", "name": "stdout", "text": "1"}],
                        "execution_count": 1,
                    }
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
        nb_path.write_text(nb_content)

        project = NbliteProject.from_path(sample_project)
        project.clean(notebooks=[nb_path], remove_outputs=True)

        cleaned = json.loads(nb_path.read_text())
        assert cleaned["cells"][0]["outputs"] == []


class TestNotebookLineage:
    def test_notebook_lineage_creation(self) -> None:
        """Test NotebookLineage creation."""
        lineage = NotebookLineage(
            source=Path("nbs/utils.ipynb"),
            code_location="nbs",
            twins={"pts": Path("pts/utils.pct.py")},
            module_path=Path("mypackage/utils.py"),
        )
        assert lineage.source == Path("nbs/utils.ipynb")
        assert lineage.code_location == "nbs"
        assert "pts" in lineage.twins
        assert lineage.module_path == Path("mypackage/utils.py")

    def test_notebook_lineage_defaults(self) -> None:
        """Test NotebookLineage default values."""
        lineage = NotebookLineage(
            source=Path("test.ipynb"),
            code_location="nbs",
        )
        assert lineage.twins == {}
        assert lineage.module_path is None

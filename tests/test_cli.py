"""
Tests for the CLI (Milestone 8).
"""

import json
import os
from pathlib import Path

import click
import pytest
from typer.testing import CliRunner

from nblite.cli.app import app

runner = CliRunner()


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a complete sample project."""
    # Create directories
    (tmp_path / "nbs").mkdir()
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
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )
    (tmp_path / "nbs" / "utils.ipynb").write_text(nb_content)

    # Create config
    config_content = """
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mypackage"
format = "module"
"""
    (tmp_path / "nblite.toml").write_text(config_content)

    return tmp_path


class TestCLIBasics:
    def test_version(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "nblite" in result.output.lower() or "0." in result.output

    def test_help(self) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "export" in result.output
        assert "clean" in result.output

    def test_no_args_shows_help(self) -> None:
        """Test that no args shows help."""
        result = runner.invoke(app)
        # Typer returns exit code 0 or 2 for help display
        assert result.exit_code in (0, 2)
        assert "nblite" in result.output.lower()


class TestInitCommand:
    def test_init_creates_config(self, tmp_path: Path) -> None:
        """Test nbl init creates nblite.toml."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--use-defaults"])
        assert result.exit_code == 0
        assert (tmp_path / "nblite.toml").exists()

    def test_init_with_name(self, tmp_path: Path) -> None:
        """Test nbl init with --name option."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--name", "mypackage", "--use-defaults"])
        assert result.exit_code == 0
        assert (tmp_path / "nblite.toml").exists()
        assert (tmp_path / "mypackage").exists()

    def test_init_creates_directories(self, tmp_path: Path) -> None:
        """Test nbl init creates nbs and package directories."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--name", "testpkg", "--use-defaults"])
        assert result.exit_code == 0
        assert (tmp_path / "nbs").exists()
        assert (tmp_path / "testpkg").exists()
        assert (tmp_path / "testpkg" / "__init__.py").exists()


class TestNewCommand:
    def test_new_creates_notebook(self, sample_project: Path) -> None:
        """Test nbl new creates a notebook."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["new", "nbs/api.ipynb", "-n", "api"])

        assert result.exit_code == 0
        assert (sample_project / "nbs" / "api.ipynb").exists()

    def test_new_with_title(self, sample_project: Path) -> None:
        """Test nbl new with --title option."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["new", "nbs/test.ipynb", "-n", "test", "-t", "Test Notebook"])

        assert result.exit_code == 0
        nb_path = sample_project / "nbs" / "test.ipynb"
        assert nb_path.exists()

        content = json.loads(nb_path.read_text())
        # Should have a markdown cell with title
        assert any(c.get("cell_type") == "markdown" for c in content["cells"])

    def test_new_with_no_export(self, sample_project: Path) -> None:
        """Test nbl new with --no-export option."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["new", "nbs/scratch.ipynb", "--no-export"])

        assert result.exit_code == 0
        nb_path = sample_project / "nbs" / "scratch.ipynb"
        content = json.loads(nb_path.read_text())

        # Should not have default_exp directive
        for cell in content["cells"]:
            if cell.get("cell_type") == "code":
                assert "#|default_exp" not in cell.get("source", "")

    def test_new_creates_percent_format(self, sample_project: Path) -> None:
        """Test nbl new creates percent-format notebook."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["new", "nbs/api.pct.py", "-n", "api"])

        assert result.exit_code == 0
        nb_path = sample_project / "nbs" / "api.pct.py"
        assert nb_path.exists()

        # Should be percent format (contains # %%)
        content = nb_path.read_text()
        assert "# %%" in content
        assert "#|default_exp api" in content

    def test_new_with_var_option(self, sample_project: Path) -> None:
        """Test nbl new with --var option for custom template variables."""
        os.chdir(sample_project)

        # Create a custom template that uses custom vars
        templates_dir = sample_project / "templates"
        templates_dir.mkdir(exist_ok=True)
        template_content = """# %%
#|default_exp {{ module_name }}

# %% [markdown]
# Author: {{ author }}
# Version: {{ version }}
"""
        (templates_dir / "custom.pct.py.jinja").write_text(template_content)

        result = runner.invoke(
            app,
            [
                "new",
                "nbs/test.ipynb",
                "-n",
                "test",
                "--template",
                "custom",
                "--var",
                "author=John Doe",
                "--var",
                "version=1.0.0",
            ],
        )

        assert result.exit_code == 0
        nb_path = sample_project / "nbs" / "test.ipynb"
        assert nb_path.exists()

        content = json.loads(nb_path.read_text())
        # Check the markdown cell contains the custom variables
        markdown_cells = [c for c in content["cells"] if c.get("cell_type") == "markdown"]

        # Source can be a string or list of strings in ipynb format
        def get_source(cell: dict) -> str:
            src = cell.get("source", "")
            return "".join(src) if isinstance(src, list) else src

        markdown_content = "".join(get_source(c) for c in markdown_cells)
        assert "John Doe" in markdown_content
        assert "1.0.0" in markdown_content

    def test_new_with_custom_template_file(self, sample_project: Path) -> None:
        """Test nbl new with a custom template file path."""
        os.chdir(sample_project)

        # Create a custom template
        templates_dir = sample_project / "my_templates"
        templates_dir.mkdir(exist_ok=True)
        template_content = """# %%
#|default_exp {{ module_name }}

# %% [markdown]
# # Custom Template: {{ title or module_name }}
"""
        (templates_dir / "my_template.pct.py.jinja").write_text(template_content)

        result = runner.invoke(
            app,
            [
                "new",
                "nbs/custom.ipynb",
                "-n",
                "custom",
                "--template",
                "my_templates/my_template.pct.py.jinja",
            ],
        )

        assert result.exit_code == 0
        nb_path = sample_project / "nbs" / "custom.ipynb"
        assert nb_path.exists()

        content = json.loads(nb_path.read_text())
        markdown_cells = [c for c in content["cells"] if c.get("cell_type") == "markdown"]

        # Source can be a string or list of strings in ipynb format
        def get_source(cell: dict) -> str:
            src = cell.get("source", "")
            return "".join(src) if isinstance(src, list) else src

        markdown_content = "".join(get_source(c) for c in markdown_cells)
        assert "Custom Template" in markdown_content


class TestExportCommand:
    def test_export_runs(self, sample_project: Path) -> None:
        """Test nbl export runs successfully."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["export"])

        assert result.exit_code == 0
        assert (sample_project / "mypackage" / "utils.py").exists()

    def test_export_dry_run(self, sample_project: Path) -> None:
        """Test nbl export --dry-run."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["export", "--dry-run"])

        assert result.exit_code == 0
        # Dry run should not create files
        assert not (sample_project / "mypackage" / "utils.py").exists()

    def test_export_no_project(self, tmp_path: Path) -> None:
        """Test export without project gives error."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 1

    def test_export_with_custom_pipeline(self, sample_project: Path) -> None:
        """Test nbl export --pipeline with custom pipeline."""
        os.chdir(sample_project)

        # Create pts directory for the test
        (sample_project / "pts").mkdir(exist_ok=True)

        # Add pts code location to config
        config_content = (sample_project / "nblite.toml").read_text()
        config_content += """
[cl.pts]
path = "pts"
format = "percent"
"""
        (sample_project / "nblite.toml").write_text(config_content)

        result = runner.invoke(app, ["export", "--pipeline", "nbs -> pts"])

        assert result.exit_code == 0
        assert "Using custom pipeline" in result.output
        assert (sample_project / "pts" / "utils.pct.py").exists()

    def test_export_with_reverse_pipeline(self, sample_project: Path) -> None:
        """Test nbl export --pipeline with reverse direction."""
        os.chdir(sample_project)

        # First create a pct.py file
        (sample_project / "pts").mkdir(exist_ok=True)
        pct_content = """# %% [markdown]
# # Utils

# %%
#|default_exp utils
#|export
def foo(): pass
"""
        (sample_project / "pts" / "utils.pct.py").write_text(pct_content)

        # Create output directory and add to config
        (sample_project / "nbs_out").mkdir()
        config_content = (sample_project / "nblite.toml").read_text()
        config_content += """
[cl.pts]
path = "pts"
format = "percent"

[cl.nbs_out]
path = "nbs_out"
format = "ipynb"
"""
        (sample_project / "nblite.toml").write_text(config_content)

        result = runner.invoke(app, ["export", "--pipeline", "pts -> nbs_out"])

        assert result.exit_code == 0
        assert (sample_project / "nbs_out" / "utils.ipynb").exists()


class TestCleanCommand:
    def test_clean_runs(self, sample_project: Path) -> None:
        """Test nbl clean runs."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["clean"])

        assert result.exit_code == 0


class TestConvertCommand:
    def test_convert_ipynb_to_pct(self, tmp_path: Path) -> None:
        """Test nbl convert from ipynb to pct."""
        nb_content = json.dumps(
            {
                "cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}],
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
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        pct_path = tmp_path / "test.pct.py"

        result = runner.invoke(app, ["convert", str(ipynb_path), str(pct_path)])

        assert result.exit_code == 0
        assert pct_path.exists()
        assert "# %%" in pct_path.read_text()

    def test_convert_file_not_found(self, tmp_path: Path) -> None:
        """Test convert with non-existent file."""
        result = runner.invoke(
            app, ["convert", str(tmp_path / "missing.ipynb"), str(tmp_path / "out.pct.py")]
        )
        assert result.exit_code == 1


class TestInfoCommand:
    def test_info_shows_project(self, sample_project: Path) -> None:
        """Test nbl info shows project information."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "nbs" in result.output
        assert "lib" in result.output

    def test_info_no_project(self, tmp_path: Path) -> None:
        """Test info without project gives error."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 1


class TestListCommand:
    def test_list_notebooks(self, sample_project: Path) -> None:
        """Test nbl list shows notebooks."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "utils.ipynb" in result.output

    def test_list_by_location(self, sample_project: Path) -> None:
        """Test nbl list with specific code location."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["list", "nbs"])

        assert result.exit_code == 0
        assert "utils.ipynb" in result.output

    def test_list_unknown_location(self, sample_project: Path) -> None:
        """Test nbl list with unknown code location."""
        os.chdir(sample_project)
        result = runner.invoke(app, ["list", "unknown"])

        assert result.exit_code == 1


class TestInstallDefaultTemplatesCommand:
    def test_install_default_templates_help(self) -> None:
        """Test install-default-templates --help."""
        result = runner.invoke(app, ["install-default-templates", "--help"])

        assert result.exit_code == 0
        # Use click.unstyle() to strip ANSI codes that can split text in CI
        output = click.unstyle(result.output)
        assert "Download and install default templates" in output
        assert "--overwrite" in output

    def test_install_default_templates_creates_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that install-default-templates creates the templates directory."""
        templates_dir = tmp_path / "templates"

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr(
            "nblite.templates.get_global_templates_dir",
            lambda: templates_dir,
        )

        # Mock the GitHub API response
        mock_response = [
            {"name": "test.pct.py.jinja", "type": "file"},
        ]

        def mock_fetch_github(*args, **kwargs):
            return mock_response

        def mock_download_file(*args, **kwargs):
            return b"# %% test template"

        monkeypatch.setattr(
            "nblite.cli.commands.templates._fetch_github_directory_contents",
            mock_fetch_github,
        )
        monkeypatch.setattr(
            "nblite.cli.commands.templates._download_file",
            mock_download_file,
        )

        result = runner.invoke(app, ["install-default-templates"])

        assert result.exit_code == 0
        assert templates_dir.exists()
        assert (templates_dir / "test.pct.py.jinja").exists()
        assert "Successfully installed 1 template" in result.output

    def test_install_default_templates_skips_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that existing templates are skipped without --overwrite."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir(parents=True)
        existing_template = templates_dir / "existing.pct.py.jinja"
        existing_template.write_text("# %% existing content")

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr(
            "nblite.templates.get_global_templates_dir",
            lambda: templates_dir,
        )

        # Mock the GitHub API response
        mock_response = [
            {"name": "existing.pct.py.jinja", "type": "file"},
        ]

        def mock_fetch_github(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(
            "nblite.cli.commands.templates._fetch_github_directory_contents",
            mock_fetch_github,
        )

        result = runner.invoke(app, ["install-default-templates"])

        assert result.exit_code == 0
        assert "Skipping existing.pct.py.jinja (already exists)" in result.output
        # Content should not be changed
        assert existing_template.read_text() == "# %% existing content"

    def test_install_default_templates_overwrites_with_flag(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that --overwrite replaces existing templates."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir(parents=True)
        existing_template = templates_dir / "existing.pct.py.jinja"
        existing_template.write_text("# %% old content")

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr(
            "nblite.templates.get_global_templates_dir",
            lambda: templates_dir,
        )

        # Mock the GitHub API response
        mock_response = [
            {"name": "existing.pct.py.jinja", "type": "file"},
        ]

        def mock_fetch_github(*args, **kwargs):
            return mock_response

        def mock_download_file(*args, **kwargs):
            return b"# %% new content"

        monkeypatch.setattr(
            "nblite.cli.commands.templates._fetch_github_directory_contents",
            mock_fetch_github,
        )
        monkeypatch.setattr(
            "nblite.cli.commands.templates._download_file",
            mock_download_file,
        )

        result = runner.invoke(app, ["install-default-templates", "--overwrite"])

        assert result.exit_code == 0
        # Content should be updated
        assert existing_template.read_text() == "# %% new content"
        assert "Successfully installed 1 template" in result.output

"""
Tests for Git integration (Milestone 9).
"""

import subprocess
from pathlib import Path

import pytest

from nblite.core.project import NbliteProject
from nblite.git.hooks import find_git_root, install_hooks, uninstall_hooks
from nblite.git.staging import ValidationResult, validate_staging


@pytest.fixture
def git_project(tmp_path: Path) -> Path:
    """Create a project with git initialized."""
    # Initialize git
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path)

    # Create project structure
    (tmp_path / "nbs").mkdir()
    (tmp_path / "mypackage").mkdir()

    nb_content = '{"cells": [{"cell_type": "code", "source": "#|default_exp utils\\n#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 5}'
    (tmp_path / "nbs" / "utils.ipynb").write_text(nb_content)

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


class TestFindGitRoot:
    def test_find_git_root_in_repo(self, git_project: Path) -> None:
        """Test finding git root from within repo."""
        result = find_git_root(git_project)
        assert result == git_project

    def test_find_git_root_in_subdirectory(self, git_project: Path) -> None:
        """Test finding git root from subdirectory."""
        subdir = git_project / "nbs"
        result = find_git_root(subdir)
        assert result == git_project

    def test_find_git_root_not_in_repo(self, tmp_path: Path) -> None:
        """Test finding git root when not in a repo."""
        result = find_git_root(tmp_path)
        assert result is None


class TestHookInstallation:
    def test_install_hooks(self, git_project: Path) -> None:
        """Test installing git hooks."""
        project = NbliteProject.from_path(git_project)
        install_hooks(project)

        hook_path = git_project / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        content = hook_path.read_text()
        assert "NBLITE HOOK" in content

    def test_install_hooks_preserves_existing(self, git_project: Path) -> None:
        """Test that existing hook content is preserved."""
        hook_dir = git_project / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hook_dir / "pre-commit"
        hook_path.write_text("#!/bin/sh\necho 'existing hook'\n")
        hook_path.chmod(0o755)

        project = NbliteProject.from_path(git_project)
        install_hooks(project)

        content = hook_path.read_text()
        assert "existing hook" in content
        assert "NBLITE HOOK" in content

    def test_install_hooks_idempotent(self, git_project: Path) -> None:
        """Test that installing hooks twice doesn't duplicate."""
        project = NbliteProject.from_path(git_project)
        install_hooks(project)
        install_hooks(project)

        hook_path = git_project / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()
        # Should only have one occurrence
        assert content.count("BEGIN NBLITE HOOK") == 1

    def test_uninstall_hooks(self, git_project: Path) -> None:
        """Test uninstalling git hooks."""
        project = NbliteProject.from_path(git_project)
        install_hooks(project)
        uninstall_hooks(project)

        hook_path = git_project / ".git" / "hooks" / "pre-commit"
        if hook_path.exists():
            content = hook_path.read_text()
            assert "NBLITE HOOK" not in content

    def test_uninstall_preserves_other_hooks(self, git_project: Path) -> None:
        """Test that uninstalling preserves other hook content."""
        hook_dir = git_project / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hook_dir / "pre-commit"
        hook_path.write_text("#!/bin/sh\necho 'existing hook'\n")
        hook_path.chmod(0o755)

        project = NbliteProject.from_path(git_project)
        install_hooks(project)
        uninstall_hooks(project)

        content = hook_path.read_text()
        assert "existing hook" in content
        assert "NBLITE HOOK" not in content

    def test_install_hooks_subdirectory(self, tmp_path: Path) -> None:
        """Test installing hooks for project in subdirectory."""
        # Create repo at root
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        # Create project in subdirectory
        proj_dir = tmp_path / "packages" / "myproject"
        proj_dir.mkdir(parents=True)
        (proj_dir / "nbs").mkdir()
        (proj_dir / "nblite.toml").write_text('export_pipeline = ""')

        project = NbliteProject.from_path(proj_dir)
        install_hooks(project)

        hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        content = hook_path.read_text()
        assert str(proj_dir) in content

    def test_install_hooks_not_git_repo(self, tmp_path: Path) -> None:
        """Test installing hooks fails when not in git repo."""
        (tmp_path / "nblite.toml").write_text('export_pipeline = ""')
        project = NbliteProject.from_path(tmp_path)

        with pytest.raises(RuntimeError, match="Not a git repository"):
            install_hooks(project)


class TestValidationResult:
    def test_initial_state(self) -> None:
        """Test ValidationResult starts valid."""
        result = ValidationResult()
        assert result.valid
        assert result.warnings == []
        assert result.errors == []

    def test_add_warning(self) -> None:
        """Test adding warnings doesn't invalidate."""
        result = ValidationResult()
        result.add_warning("test warning")
        assert result.valid
        assert "test warning" in result.warnings

    def test_add_error(self) -> None:
        """Test adding errors invalidates."""
        result = ValidationResult()
        result.add_error("test error")
        assert not result.valid
        assert "test error" in result.errors


class TestStagingValidation:
    def test_validate_nothing_staged(self, git_project: Path) -> None:
        """Test validation passes when nothing is staged."""
        project = NbliteProject.from_path(git_project)
        result = validate_staging(project)
        assert result.valid

    def test_validate_clean_notebook(self, git_project: Path) -> None:
        """Test validation passes for clean notebook."""
        project = NbliteProject.from_path(git_project)

        # Stage clean notebook
        subprocess.run(["git", "add", "nbs/utils.ipynb"], cwd=git_project)

        result = validate_staging(project)
        assert result.valid

    def test_validate_unclean_notebook_warns(self, git_project: Path) -> None:
        """Test validation warns for notebook with outputs."""
        # Add outputs to notebook
        nb_path = git_project / "nbs" / "utils.ipynb"
        nb_content = '{"cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": [{"output_type": "stream", "name": "stdout", "text": ["1"]}], "execution_count": 1}], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 5}'
        nb_path.write_text(nb_content)

        project = NbliteProject.from_path(git_project)
        subprocess.run(["git", "add", "nbs/utils.ipynb"], cwd=git_project)

        result = validate_staging(project)
        # Should warn about outputs
        assert len(result.warnings) > 0
        assert any("outputs" in w for w in result.warnings)

    def test_validate_missing_twin_warns(self, git_project: Path) -> None:
        """Test validation warns when twin is not staged."""
        project = NbliteProject.from_path(git_project)

        # Export to create twins
        project.export()

        # Stage only the notebook, not the generated module
        subprocess.run(["git", "add", "nbs/utils.ipynb"], cwd=git_project)

        result = validate_staging(project)
        # Should warn about missing twin
        assert len(result.warnings) > 0
        assert any("twin" in w.lower() for w in result.warnings)

    def test_validate_twins_staged_together(self, git_project: Path) -> None:
        """Test validation passes when twins are staged together."""
        project = NbliteProject.from_path(git_project)

        # Export to create twins
        project.export()

        # Stage both notebook and generated module
        subprocess.run(["git", "add", "nbs/utils.ipynb", "mypackage/utils.py"], cwd=git_project)

        result = validate_staging(project)
        # Should not have twin-related warnings
        assert not any("twin" in w.lower() for w in result.warnings)

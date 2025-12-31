"""
Tests for package setup and imports (Milestone 1).
"""


def test_package_imports() -> None:
    """Verify all main modules can be imported."""
    import nblite
    from nblite import cli, config, core, docs, export, extensions, git, sync, utils

    # Verify modules are accessible
    assert nblite is not None
    assert core is not None
    assert config is not None
    assert export is not None
    assert git is not None
    assert docs is not None
    assert extensions is not None
    assert cli is not None
    assert sync is not None
    assert utils is not None


def test_version_defined() -> None:
    """Verify package version is defined."""
    import nblite

    assert hasattr(nblite, "__version__")
    assert nblite.__version__
    assert isinstance(nblite.__version__, str)


def test_notebookx_available() -> None:
    """Verify notebookx dependency is available."""
    import notebookx

    assert hasattr(notebookx, "Notebook")


def test_cli_app_exists() -> None:
    """Verify CLI app is defined."""
    from nblite.cli import app, main

    assert app is not None
    assert main is not None
    assert callable(main)


def test_pydantic_available() -> None:
    """Verify pydantic dependency is available."""
    import pydantic

    assert hasattr(pydantic, "BaseModel")


def test_typer_available() -> None:
    """Verify typer dependency is available."""
    import typer

    assert hasattr(typer, "Typer")


def test_rich_available() -> None:
    """Verify rich dependency is available."""
    import rich

    assert hasattr(rich, "print")


def test_jinja2_available() -> None:
    """Verify jinja2 dependency is available."""
    import jinja2

    assert hasattr(jinja2, "Template")

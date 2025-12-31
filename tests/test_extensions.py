"""
Tests for extension system (Milestone 10).
"""

from pathlib import Path

import pytest

from nblite.extensions.hooks import HookRegistry, HookType, hook
from nblite.extensions.loader import load_extension, load_extensions


class TestHookType:
    def test_hook_types_exist(self) -> None:
        """Test all expected hook types exist."""
        expected = [
            "PRE_EXPORT",
            "POST_EXPORT",
            "PRE_NOTEBOOK_EXPORT",
            "POST_NOTEBOOK_EXPORT",
            "PRE_CELL_EXPORT",
            "POST_CELL_EXPORT",
            "PRE_CLEAN",
            "POST_CLEAN",
            "DIRECTIVE_PARSED",
        ]
        for hook_name in expected:
            assert hasattr(HookType, hook_name)

    def test_hook_type_values(self) -> None:
        """Test hook type enum values."""
        assert HookType.PRE_EXPORT.value == "pre_export"
        assert HookType.POST_EXPORT.value == "post_export"


class TestHookRegistry:
    def setup_method(self) -> None:
        """Clear registry before each test."""
        HookRegistry.clear()

    def test_register_hook(self) -> None:
        """Test registering a hook callback."""
        called = []

        def my_hook(**kwargs):  # type: ignore[no-untyped-def]
            called.append(True)

        HookRegistry.register(HookType.PRE_EXPORT, my_hook)
        HookRegistry.trigger(HookType.PRE_EXPORT)

        assert len(called) == 1

    def test_hook_decorator(self) -> None:
        """Test @hook decorator."""
        called = []

        @hook(HookType.POST_EXPORT)
        def after_export(**kwargs):  # type: ignore[no-untyped-def]
            called.append(True)

        HookRegistry.trigger(HookType.POST_EXPORT)

        assert len(called) == 1

    def test_hook_receives_context(self) -> None:
        """Test that hook receives context kwargs."""
        received: dict[str, str] = {}

        @hook(HookType.PRE_NOTEBOOK_EXPORT)
        def before_nb(**kwargs):  # type: ignore[no-untyped-def]
            received.update(kwargs)

        HookRegistry.trigger(HookType.PRE_NOTEBOOK_EXPORT, notebook="test", path="/test")

        assert received["notebook"] == "test"
        assert received["path"] == "/test"

    def test_multiple_hooks_same_type(self) -> None:
        """Test multiple hooks for same type."""
        results: list[int] = []

        @hook(HookType.PRE_EXPORT)
        def hook1(**kwargs):  # type: ignore[no-untyped-def]
            results.append(1)

        @hook(HookType.PRE_EXPORT)
        def hook2(**kwargs):  # type: ignore[no-untyped-def]
            results.append(2)

        HookRegistry.trigger(HookType.PRE_EXPORT)

        assert results == [1, 2]

    def test_clear_all_hooks(self) -> None:
        """Test clearing all hooks."""
        called = []

        @hook(HookType.PRE_EXPORT)
        def my_hook(**kwargs):  # type: ignore[no-untyped-def]
            called.append(True)

        HookRegistry.clear()
        HookRegistry.trigger(HookType.PRE_EXPORT)

        assert len(called) == 0

    def test_clear_specific_hook_type(self) -> None:
        """Test clearing specific hook type."""
        pre_called = []
        post_called = []

        @hook(HookType.PRE_EXPORT)
        def pre_hook(**kwargs):  # type: ignore[no-untyped-def]
            pre_called.append(True)

        @hook(HookType.POST_EXPORT)
        def post_hook(**kwargs):  # type: ignore[no-untyped-def]
            post_called.append(True)

        HookRegistry.clear(HookType.PRE_EXPORT)

        HookRegistry.trigger(HookType.PRE_EXPORT)
        HookRegistry.trigger(HookType.POST_EXPORT)

        assert len(pre_called) == 0
        assert len(post_called) == 1

    def test_get_hooks(self) -> None:
        """Test getting registered hooks."""

        @hook(HookType.PRE_EXPORT)
        def my_hook(**kwargs):  # type: ignore[no-untyped-def]
            pass

        hooks = HookRegistry.get_hooks(HookType.PRE_EXPORT)
        assert len(hooks) == 1
        assert hooks[0] == my_hook

    def test_trigger_returns_results(self) -> None:
        """Test that trigger returns callback results."""

        @hook(HookType.PRE_EXPORT)
        def returns_value(**kwargs):  # type: ignore[no-untyped-def]
            return "result"

        results = HookRegistry.trigger(HookType.PRE_EXPORT)
        assert results == ["result"]


class TestExtensionLoader:
    def setup_method(self) -> None:
        """Clear registry before each test."""
        HookRegistry.clear()

    def test_load_from_file(self, tmp_path: Path) -> None:
        """Test loading extension from file path."""
        ext_content = """
from nblite.extensions import hook, HookType

LOADED = True

@hook(HookType.PRE_EXPORT)
def my_hook(**kwargs):
    pass
"""
        ext_path = tmp_path / "my_extension.py"
        ext_path.write_text(ext_content)

        module = load_extension(path=str(ext_path))

        # Verify module was loaded
        assert hasattr(module, "LOADED")
        assert module.LOADED is True

        # Verify hook was registered
        assert len(HookRegistry.get_hooks(HookType.PRE_EXPORT)) == 1

    def test_load_from_pathlib(self, tmp_path: Path) -> None:
        """Test loading with pathlib.Path object."""
        ext_content = "LOADED = True"
        ext_path = tmp_path / "ext.py"
        ext_path.write_text(ext_content)

        module = load_extension(path=ext_path)
        assert module.LOADED is True

    def test_load_multiple_extensions(self, tmp_path: Path) -> None:
        """Test loading multiple extensions."""
        ext1 = tmp_path / "ext1.py"
        ext1.write_text("""
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def hook1(**kwargs): pass
""")

        ext2 = tmp_path / "ext2.py"
        ext2.write_text("""
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def hook2(**kwargs): pass
""")

        load_extension(path=str(ext1))
        load_extension(path=str(ext2))

        assert len(HookRegistry.get_hooks(HookType.PRE_EXPORT)) == 2

    def test_load_extensions_list(self, tmp_path: Path) -> None:
        """Test load_extensions with list of specs."""
        ext1 = tmp_path / "ext1.py"
        ext1.write_text("VALUE1 = 1")

        ext2 = tmp_path / "ext2.py"
        ext2.write_text("VALUE2 = 2")

        modules = load_extensions(
            [
                {"path": str(ext1)},
                {"path": str(ext2)},
            ]
        )

        assert len(modules) == 2
        assert modules[0].VALUE1 == 1
        assert modules[1].VALUE2 == 2

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_extension(path=str(tmp_path / "nonexistent.py"))

    def test_load_directory_raises(self, tmp_path: Path) -> None:
        """Test loading directory raises error."""
        with pytest.raises(ValueError, match="not a file"):
            load_extension(path=str(tmp_path))

    def test_load_no_args_raises(self) -> None:
        """Test load_extension without args raises error."""
        with pytest.raises(ValueError, match="Either path or module"):
            load_extension()

    def test_load_both_args_raises(self, tmp_path: Path) -> None:
        """Test load_extension with both args raises error."""
        ext = tmp_path / "ext.py"
        ext.write_text("")

        with pytest.raises(ValueError, match="Only one of"):
            load_extension(path=str(ext), module="some.module")

    def test_load_from_module(self) -> None:
        """Test loading from Python module path."""
        # Load a known module from the standard library
        module = load_extension(module="json")
        assert hasattr(module, "dumps")

    def test_load_invalid_module(self) -> None:
        """Test loading non-existent module raises error."""
        with pytest.raises(ImportError):
            load_extension(module="nonexistent.module.path")


class TestExtensionIntegration:
    """Integration tests for extensions with projects."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        HookRegistry.clear()

    def teardown_method(self) -> None:
        """Clear registry after each test."""
        HookRegistry.clear()

    def test_extension_variables_accessible(self, tmp_path: Path) -> None:
        """Test that extension module variables are accessible."""
        ext_content = """
CONFIG = {"key": "value"}
counter = 0

def increment():
    global counter
    counter += 1
"""
        ext_path = tmp_path / "ext.py"
        ext_path.write_text(ext_content)

        module = load_extension(path=str(ext_path))

        assert module.CONFIG == {"key": "value"}
        assert module.counter == 0
        module.increment()
        assert module.counter == 1


class TestProjectExtensionLoading:
    """Tests for extension loading via NbliteProject."""

    def setup_method(self) -> None:
        """Clear hooks before each test."""
        HookRegistry.clear()

    def teardown_method(self) -> None:
        """Clear hooks after each test."""
        HookRegistry.clear()

    def test_project_loads_extensions(self, tmp_path: Path) -> None:
        """Test that NbliteProject loads extensions from config."""
        from nblite.core.project import NbliteProject

        # Create extension
        ext_file = tmp_path / "my_ext.py"
        ext_file.write_text("""
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def before_export(**kwargs):
    pass
""")

        # Create config with extension
        config_file = tmp_path / "nblite.toml"
        config_file.write_text("""
[[extensions]]
path = "my_ext.py"

[cl.nbs]
path = "nbs"
format = "ipynb"
""")

        # Create nbs directory
        (tmp_path / "nbs").mkdir()

        # Load project
        project = NbliteProject.from_path(tmp_path)

        # Hook should be registered
        hooks = HookRegistry.get_hooks(HookType.PRE_EXPORT)
        assert len(hooks) == 1
        assert len(project._loaded_extensions) == 1


class TestExportHooks:
    """Tests for export hooks being triggered."""

    def setup_method(self) -> None:
        """Clear hooks before each test."""
        HookRegistry.clear()

    def teardown_method(self) -> None:
        """Clear hooks after each test."""
        HookRegistry.clear()

    def test_pre_and_post_export_hooks(self, tmp_path: Path) -> None:
        """Test PRE_EXPORT and POST_EXPORT hooks are triggered."""
        import json

        from nblite.core.project import NbliteProject

        hook_calls = []

        @hook(HookType.PRE_EXPORT)
        def pre_export(**kwargs):
            hook_calls.append(("pre_export", kwargs.get("project")))

        @hook(HookType.POST_EXPORT)
        def post_export(**kwargs):
            hook_calls.append(("post_export", kwargs.get("result")))

        # Create project
        (tmp_path / "nbs").mkdir()
        (tmp_path / "lib").mkdir()

        config_file = tmp_path / "nblite.toml"
        config_file.write_text("""
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "lib"
format = "module"
""")

        # Create a notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test\n#|export\ndef foo(): pass",
                        "metadata": {},
                        "outputs": [],
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
        (tmp_path / "nbs" / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(tmp_path)
        project.export()

        # Both hooks should have been called
        assert len(hook_calls) == 2
        assert hook_calls[0][0] == "pre_export"
        assert hook_calls[0][1] == project
        assert hook_calls[1][0] == "post_export"

    def test_notebook_export_hooks(self, tmp_path: Path) -> None:
        """Test PRE_NOTEBOOK_EXPORT and POST_NOTEBOOK_EXPORT hooks."""
        import json

        from nblite.core.project import NbliteProject

        hook_calls = []

        @hook(HookType.PRE_NOTEBOOK_EXPORT)
        def pre_nb(**kwargs):
            hook_calls.append(("pre", kwargs.get("notebook")))

        @hook(HookType.POST_NOTEBOOK_EXPORT)
        def post_nb(**kwargs):
            hook_calls.append(("post", kwargs.get("success")))

        # Create project
        (tmp_path / "nbs").mkdir()
        (tmp_path / "lib").mkdir()

        config_file = tmp_path / "nblite.toml"
        config_file.write_text("""
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "lib"
format = "module"
""")

        # Create a notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test\n#|export\ndef foo(): pass",
                        "metadata": {},
                        "outputs": [],
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
        (tmp_path / "nbs" / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(tmp_path)
        project.export()

        # Should have pre and post for the notebook
        assert any(call[0] == "pre" for call in hook_calls)
        assert any(call[0] == "post" and call[1] is True for call in hook_calls)


class TestCleanHooks:
    """Tests for clean hooks being triggered."""

    def setup_method(self) -> None:
        """Clear hooks before each test."""
        HookRegistry.clear()

    def teardown_method(self) -> None:
        """Clear hooks after each test."""
        HookRegistry.clear()

    def test_pre_and_post_clean_hooks(self, tmp_path: Path) -> None:
        """Test PRE_CLEAN and POST_CLEAN hooks are triggered."""
        import json

        from nblite.core.project import NbliteProject

        hook_calls = []

        @hook(HookType.PRE_CLEAN)
        def pre_clean(**kwargs):
            hook_calls.append("pre_clean")

        @hook(HookType.POST_CLEAN)
        def post_clean(**kwargs):
            hook_calls.append(("post_clean", kwargs.get("cleaned_notebooks")))

        # Create project
        (tmp_path / "nbs").mkdir()

        config_file = tmp_path / "nblite.toml"
        config_file.write_text("""
[cl.nbs]
path = "nbs"
format = "ipynb"
""")

        # Create a notebook
        nb_content = json.dumps(
            {
                "cells": [
                    {"cell_type": "code", "source": "print('hello')", "metadata": {}, "outputs": []}
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
        (tmp_path / "nbs" / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(tmp_path)
        project.clean()

        assert "pre_clean" in hook_calls
        assert any(isinstance(c, tuple) and c[0] == "post_clean" for c in hook_calls)


class TestDirectiveHooks:
    """Tests for directive parsing hooks being triggered."""

    def setup_method(self) -> None:
        """Clear hooks before each test."""
        HookRegistry.clear()

    def teardown_method(self) -> None:
        """Clear hooks after each test."""
        HookRegistry.clear()

    def test_directive_parsed_hook(self) -> None:
        """Test DIRECTIVE_PARSED hook is triggered for each directive."""
        from nblite.core.directive import parse_directives_from_source

        parsed_directives = []

        @hook(HookType.DIRECTIVE_PARSED)
        def on_directive(**kwargs):
            parsed_directives.append(kwargs.get("directive").name)

        source = """#|default_exp mymodule
#|export
def foo():
    pass
"""
        parse_directives_from_source(source)

        assert "default_exp" in parsed_directives
        assert "export" in parsed_directives


class TestCellExportHooks:
    """Tests for cell-level export hooks being triggered."""

    def setup_method(self) -> None:
        """Clear hooks before each test."""
        HookRegistry.clear()

    def teardown_method(self) -> None:
        """Clear hooks after each test."""
        HookRegistry.clear()

    def test_cell_export_hooks(self, tmp_path: Path) -> None:
        """Test PRE_CELL_EXPORT and POST_CELL_EXPORT hooks."""
        import json

        from nblite.core.project import NbliteProject

        cell_exports = []

        @hook(HookType.PRE_CELL_EXPORT)
        def pre_cell(**kwargs):
            cell_exports.append(("pre", kwargs.get("cell").index))

        @hook(HookType.POST_CELL_EXPORT)
        def post_cell(**kwargs):
            cell_exports.append(("post", kwargs.get("source")))

        # Create project with notebook
        config_file = tmp_path / "nblite.toml"
        config_file.write_text("""
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "lib"
format = "module"
""")
        (tmp_path / "nbs").mkdir()
        (tmp_path / "lib").mkdir()

        # Create notebook with exportable cells (using JSON)
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp test",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef foo(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef bar(): pass",
                        "metadata": {},
                        "outputs": [],
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
        (tmp_path / "nbs" / "test.ipynb").write_text(nb_content)

        project = NbliteProject.from_path(tmp_path)
        project.export()

        # Should have pre and post for each exported cell
        pre_calls = [c for c in cell_exports if c[0] == "pre"]
        post_calls = [c for c in cell_exports if c[0] == "post"]
        assert len(pre_calls) >= 2  # At least 2 exported cells
        assert len(post_calls) >= 2

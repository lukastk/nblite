"""
Tests for advanced features (Milestone 13).
"""

from pathlib import Path

import pytest

from nblite.cli.commands.from_module import module_to_notebook, modules_to_notebooks
from nblite.core.notebook import Notebook
from nblite.templates.renderer import (
    get_builtin_templates,
    infer_template_format,
    render_template,
    render_template_string,
)


class TestTemplates:
    def test_render_template_string(self) -> None:
        """Test rendering a template string."""
        result = render_template_string("#|default_exp {{ module_name }}", module_name="utils")
        assert result == "#|default_exp utils"

    def test_render_template_string_multiple_vars(self) -> None:
        """Test rendering with multiple variables."""
        result = render_template_string(
            "def {{ func_name }}({{ args }}): pass", func_name="process", args="x, y"
        )
        assert result == "def process(x, y): pass"

    def test_render_template_file(self, tmp_path: Path) -> None:
        """Test rendering a template file."""
        template_content = """# %%
#|default_exp {{ module_name }}

# %%
#|export
def {{ function_name }}():
    \"\"\"{{ description }}\"\"\"
    pass
"""
        template_path = tmp_path / "test.pct.py.jinja"
        template_path.write_text(template_content)

        result = render_template(
            template_path, module_name="utils", function_name="process", description="Process data"
        )

        assert "#|default_exp utils" in result
        assert "def process():" in result
        assert "Process data" in result

    def test_render_template_file_not_found(self, tmp_path: Path) -> None:
        """Test rendering non-existent template raises error."""
        with pytest.raises(FileNotFoundError):
            render_template(tmp_path / "nonexistent.jinja")

    def test_get_builtin_templates(self) -> None:
        """Test getting built-in templates."""
        templates = get_builtin_templates()
        assert "default" in templates
        assert "script" in templates
        assert "#|default_exp" in templates["default"]

    def test_builtin_default_template(self) -> None:
        """Test the default builtin template."""
        templates = get_builtin_templates()
        result = render_template_string(
            templates["default"], module_name="mymodule", title="My Module"
        )
        assert "#|default_exp mymodule" in result
        assert "# My Module" in result

    def test_builtin_script_template(self) -> None:
        """Test the script builtin template."""
        templates = get_builtin_templates()
        result = render_template_string(
            templates["script"], module_name="workflow", function_name="run", args="input_path: str"
        )
        assert "#|default_exp workflow" in result
        assert "#|export_as_func true" in result
        assert "def run(input_path: str):" in result

    def test_builtin_default_template_no_export(self) -> None:
        """Test the default template with no_export=True."""
        templates = get_builtin_templates()
        result = render_template_string(
            templates["default"], module_name="mymodule", title="My Module", no_export=True
        )
        # When no_export=True, the default_exp directive should not appear
        assert "#|default_exp" not in result
        assert "# My Module" in result

    def test_builtin_script_template_no_export(self) -> None:
        """Test the script template with no_export=True."""
        templates = get_builtin_templates()
        result = render_template_string(templates["script"], module_name="workflow", no_export=True)
        # When no_export=True, the default_exp directive should not appear
        assert "#|default_exp" not in result
        # But export_as_func should still be there
        assert "#|export_as_func true" in result

    def test_infer_template_format_ipynb(self) -> None:
        """Test inferring ipynb format from extension."""
        assert infer_template_format("template.ipynb.jinja") == "ipynb"
        assert infer_template_format("template.ipynb") == "ipynb"

    def test_infer_template_format_percent(self) -> None:
        """Test inferring percent format from extension."""
        assert infer_template_format("template.pct.py.jinja") == "percent"
        assert infer_template_format("template.pct.py") == "percent"
        assert infer_template_format("template.py.jinja") == "percent"
        assert infer_template_format("template.py") == "percent"

    def test_infer_template_format_default(self) -> None:
        """Test default format for unknown extensions."""
        assert infer_template_format("template.txt.jinja") == "percent"
        assert infer_template_format("template.jinja") == "percent"

    def test_render_template_with_dest_fmt(self, tmp_path: Path) -> None:
        """Test rendering template with format conversion."""
        # Create a percent-format template
        template_content = """# %%
#|default_exp {{ module_name }}

# %% [markdown]
# # {{ title }}

# %%
#|export
def hello():
    pass
"""
        template_path = tmp_path / "test.pct.py.jinja"
        template_path.write_text(template_content)

        # Render to ipynb format
        result = render_template(
            template_path, dest_fmt="ipynb", module_name="utils", title="Utils Module"
        )

        # Should be valid JSON (ipynb format)
        import json

        nb_data = json.loads(result)
        assert "cells" in nb_data
        assert nb_data["nbformat"] == 4

    def test_render_template_same_format(self, tmp_path: Path) -> None:
        """Test rendering template without format conversion."""
        template_content = """# %%
#|default_exp {{ module_name }}
"""
        template_path = tmp_path / "test.pct.py.jinja"
        template_path.write_text(template_content)

        # Render to same format (percent)
        result = render_template(template_path, dest_fmt="percent", module_name="utils")

        # Should still be percent format
        assert "# %%" in result
        assert "#|default_exp utils" in result


class TestFromModule:
    def test_convert_module_to_notebook(self, tmp_path: Path) -> None:
        """Test converting Python module to notebook."""
        module_content = '''
def foo():
    """Do foo."""
    pass

def bar():
    """Do bar."""
    pass
'''
        module_path = tmp_path / "utils.py"
        module_path.write_text(module_content)

        nb_path = tmp_path / "utils.ipynb"
        module_to_notebook(module_path, nb_path, module_name="utils")

        assert nb_path.exists()

        nb = Notebook.from_file(nb_path)
        assert nb.default_exp == "utils"

    def test_module_with_imports(self, tmp_path: Path) -> None:
        """Test module with imports is converted correctly."""
        module_content = """
import os
from pathlib import Path

def process(path: str):
    return Path(path)
"""
        module_path = tmp_path / "utils.py"
        module_path.write_text(module_content)

        nb_path = tmp_path / "utils.ipynb"
        module_to_notebook(module_path, nb_path)

        nb = Notebook.from_file(nb_path)

        # Check imports are in a cell
        sources = [c.source for c in nb.cells]
        import_found = any("import os" in s for s in sources)
        assert import_found

    def test_module_with_docstring(self, tmp_path: Path) -> None:
        """Test module docstring is preserved in source."""
        module_content = '''"""
This is the module docstring.
It describes what the module does.
"""

def foo():
    pass
'''
        module_path = tmp_path / "utils.py"
        module_path.write_text(module_content)

        nb_path = tmp_path / "utils.ipynb"
        module_to_notebook(module_path, nb_path)

        nb = Notebook.from_file(nb_path)

        # Check that docstring is preserved in the source (not as separate markdown)
        sources = [c.source for c in nb.cells]
        docstring_found = any("module docstring" in s for s in sources)
        assert docstring_found

    def test_module_with_class(self, tmp_path: Path) -> None:
        """Test module with class is converted correctly."""
        module_content = '''
class MyClass:
    """A class."""
    def __init__(self):
        self.value = 0

    def method(self):
        return self.value
'''
        module_path = tmp_path / "myclass.py"
        module_path.write_text(module_content)

        nb_path = tmp_path / "myclass.ipynb"
        module_to_notebook(module_path, nb_path)

        nb = Notebook.from_file(nb_path)

        # Check class is exported
        sources = [c.source for c in nb.cells]
        class_found = any("class MyClass:" in s for s in sources)
        assert class_found

    def test_module_to_percent_format(self, tmp_path: Path) -> None:
        """Test converting module to percent format."""
        module_content = """
def foo():
    pass
"""
        module_path = tmp_path / "utils.py"
        module_path.write_text(module_content)

        nb_path = tmp_path / "utils.pct.py"
        module_to_notebook(module_path, nb_path, format="percent")

        assert nb_path.exists()
        content = nb_path.read_text()
        assert "# %%" in content
        assert "#|default_exp" in content

    def test_module_not_found(self, tmp_path: Path) -> None:
        """Test error when module doesn't exist."""
        with pytest.raises(FileNotFoundError):
            module_to_notebook(tmp_path / "nonexistent.py", tmp_path / "out.ipynb")

    def test_default_module_name_from_filename(self, tmp_path: Path) -> None:
        """Test module name defaults to filename."""
        module_path = tmp_path / "my_utils.py"
        module_path.write_text("x = 1")

        nb_path = tmp_path / "my_utils.ipynb"
        module_to_notebook(module_path, nb_path)

        nb = Notebook.from_file(nb_path)
        assert nb.default_exp == "my_utils"

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test output directory is created."""
        module_path = tmp_path / "utils.py"
        module_path.write_text("x = 1")

        nb_path = tmp_path / "subdir" / "nested" / "utils.ipynb"
        module_to_notebook(module_path, nb_path)

        assert nb_path.exists()

    def test_modules_to_notebooks_basic(self, tmp_path: Path) -> None:
        """Test converting a directory of modules."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()

        (input_dir / "utils.py").write_text("def foo(): pass")
        (input_dir / "core.py").write_text("def bar(): pass")

        output_dir = tmp_path / "nbs"

        created = modules_to_notebooks(input_dir, output_dir)

        assert len(created) == 2
        assert (output_dir / "utils.ipynb").exists()
        assert (output_dir / "core.ipynb").exists()

    def test_modules_to_notebooks_recursive(self, tmp_path: Path) -> None:
        """Test recursive conversion."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()
        subdir = input_dir / "sub"
        subdir.mkdir()

        (input_dir / "utils.py").write_text("def foo(): pass")
        (subdir / "helper.py").write_text("def bar(): pass")

        output_dir = tmp_path / "nbs"

        created = modules_to_notebooks(input_dir, output_dir, recursive=True)

        assert len(created) == 2
        assert (output_dir / "utils.ipynb").exists()
        assert (output_dir / "sub" / "helper.ipynb").exists()

    def test_modules_to_notebooks_non_recursive(self, tmp_path: Path) -> None:
        """Test non-recursive conversion."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()
        subdir = input_dir / "sub"
        subdir.mkdir()

        (input_dir / "utils.py").write_text("def foo(): pass")
        (subdir / "helper.py").write_text("def bar(): pass")

        output_dir = tmp_path / "nbs"

        created = modules_to_notebooks(input_dir, output_dir, recursive=False)

        assert len(created) == 1
        assert (output_dir / "utils.ipynb").exists()
        assert not (output_dir / "sub" / "helper.ipynb").exists()

    def test_modules_to_notebooks_exclude_init(self, tmp_path: Path) -> None:
        """Test that __init__.py is excluded by default."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()

        (input_dir / "utils.py").write_text("def foo(): pass")
        (input_dir / "__init__.py").write_text("# init")

        output_dir = tmp_path / "nbs"

        created = modules_to_notebooks(input_dir, output_dir, exclude_init=True)

        assert len(created) == 1
        assert (output_dir / "utils.ipynb").exists()
        assert not (output_dir / "__init__.ipynb").exists()

    def test_modules_to_notebooks_include_init(self, tmp_path: Path) -> None:
        """Test including __init__.py files."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()

        (input_dir / "utils.py").write_text("def foo(): pass")
        (input_dir / "__init__.py").write_text("# init")

        output_dir = tmp_path / "nbs"

        created = modules_to_notebooks(input_dir, output_dir, exclude_init=False)

        assert len(created) == 2
        assert (output_dir / "utils.ipynb").exists()
        assert (output_dir / "__init__.ipynb").exists()

    def test_modules_to_notebooks_percent_format(self, tmp_path: Path) -> None:
        """Test converting to percent format."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()

        (input_dir / "utils.py").write_text("def foo(): pass")

        output_dir = tmp_path / "nbs"

        created = modules_to_notebooks(input_dir, output_dir, format="percent")

        assert len(created) == 1
        assert (output_dir / "utils.pct.py").exists()

    def test_modules_to_notebooks_module_name_from_path(self, tmp_path: Path) -> None:
        """Test module name is derived from relative path."""
        input_dir = tmp_path / "src"
        input_dir.mkdir()
        subdir = input_dir / "sub"
        subdir.mkdir()

        (subdir / "helper.py").write_text("def bar(): pass")

        output_dir = tmp_path / "nbs"

        modules_to_notebooks(input_dir, output_dir)

        nb = Notebook.from_file(output_dir / "sub" / "helper.ipynb")
        assert nb.default_exp == "sub.helper"

    def test_modules_to_notebooks_not_a_directory(self, tmp_path: Path) -> None:
        """Test error when input is not a directory."""
        file_path = tmp_path / "file.py"
        file_path.write_text("x = 1")

        with pytest.raises(NotADirectoryError):
            modules_to_notebooks(file_path, tmp_path / "out")

    def test_modules_to_notebooks_directory_not_found(self, tmp_path: Path) -> None:
        """Test error when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            modules_to_notebooks(tmp_path / "nonexistent", tmp_path / "out")


class TestGlobalTemplates:
    def test_get_global_templates_dir(self) -> None:
        """Test that get_global_templates_dir returns expected path."""
        from nblite.templates import get_global_templates_dir

        result = get_global_templates_dir()
        assert result == Path.home() / ".config" / "nblite" / "templates"

    def test_find_template_searches_global_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _find_template searches global templates directory."""
        from nblite.cli.commands.new import _find_template

        # Create a mock global templates directory
        global_templates = tmp_path / "global_templates"
        global_templates.mkdir()
        template_file = global_templates / "my_template.pct.py.jinja"
        template_file.write_text("# %% global template")

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr("nblite.templates.get_global_templates_dir", lambda: global_templates)

        # Search without a project root (should find in global)
        found_path, builtin_content = _find_template("my_template", project_root=None)

        assert found_path == template_file
        assert builtin_content is None

    def test_project_templates_take_precedence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that project templates take precedence over global templates."""
        from nblite.cli.commands.new import _find_template

        # Create a mock global templates directory
        global_templates = tmp_path / "global_templates"
        global_templates.mkdir()
        global_template = global_templates / "shared.pct.py.jinja"
        global_template.write_text("# %% global version")

        # Create a project templates directory
        project_root = tmp_path / "project"
        project_root.mkdir()
        project_templates = project_root / "templates"
        project_templates.mkdir()
        project_template = project_templates / "shared.pct.py.jinja"
        project_template.write_text("# %% project version")

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr("nblite.templates.get_global_templates_dir", lambda: global_templates)

        # Search with project root - should find project template
        found_path, builtin_content = _find_template("shared", project_root=project_root)

        assert found_path == project_template
        assert builtin_content is None
        assert "project version" in found_path.read_text()

    def test_global_templates_fallback_to_builtin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that builtin templates are used when no file templates found."""
        from nblite.cli.commands.new import _find_template

        # Create empty global templates directory
        global_templates = tmp_path / "global_templates"
        global_templates.mkdir()

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr("nblite.templates.get_global_templates_dir", lambda: global_templates)

        # Search for builtin template "default"
        found_path, builtin_content = _find_template("default", project_root=None)

        assert found_path is None
        assert builtin_content is not None
        assert "#|default_exp" in builtin_content

    def test_find_template_nonexistent_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _find_template returns None for nonexistent templates."""
        from nblite.cli.commands.new import _find_template

        # Create empty global templates directory
        global_templates = tmp_path / "global_templates"
        global_templates.mkdir()

        # Patch get_global_templates_dir at the source module
        monkeypatch.setattr("nblite.templates.get_global_templates_dir", lambda: global_templates)

        # Search for nonexistent template
        found_path, builtin_content = _find_template("nonexistent_template", project_root=None)

        assert found_path is None
        assert builtin_content is None

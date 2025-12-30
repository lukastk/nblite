"""
Tests for advanced features (Milestone 13).
"""

from pathlib import Path

import pytest

from nblite.cli.from_module import module_to_notebook
from nblite.core.notebook import Notebook
from nblite.templates.renderer import (
    get_builtin_templates,
    render_template,
    render_template_string,
)


class TestTemplates:
    def test_render_template_string(self) -> None:
        """Test rendering a template string."""
        result = render_template_string(
            "#|default_exp {{ module_name }}",
            module_name="utils"
        )
        assert result == "#|default_exp utils"

    def test_render_template_string_multiple_vars(self) -> None:
        """Test rendering with multiple variables."""
        result = render_template_string(
            "def {{ func_name }}({{ args }}): pass",
            func_name="process",
            args="x, y"
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
            template_path,
            module_name="utils",
            function_name="process",
            description="Process data"
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
            templates["default"],
            module_name="mymodule",
            title="My Module"
        )
        assert "#|default_exp mymodule" in result
        assert "# My Module" in result

    def test_builtin_script_template(self) -> None:
        """Test the script builtin template."""
        templates = get_builtin_templates()
        result = render_template_string(
            templates["script"],
            module_name="workflow",
            function_name="run",
            args="input_path: str"
        )
        assert "#|default_exp workflow" in result
        assert "#|export_as_func true" in result
        assert "def run(input_path: str):" in result


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
        module_content = '''
import os
from pathlib import Path

def process(path: str):
    return Path(path)
'''
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
        """Test module docstring becomes markdown cell."""
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

        # Check there's a markdown cell with docstring
        markdown_cells = [c for c in nb.cells if c.cell_type == "markdown"]
        assert len(markdown_cells) > 0
        assert "module docstring" in markdown_cells[0].source

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
        module_content = '''
def foo():
    pass
'''
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

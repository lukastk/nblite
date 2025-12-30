# nblite v2 - Development TODO

This document tracks the implementation progress of nblite v2. Each milestone has specific tasks and pytest tests to verify completion.

---

## Milestone 1: Project Setup & Core Infrastructure

### Tasks

- [ ] Initialize Python package with `pyproject.toml`
  - [ ] Set up dependencies: notebookx, pydantic, typer, rich, jinja2, tomli
  - [ ] Set up dev dependencies: pytest, pytest-cov, ruff, mypy
  - [ ] Configure ruff for linting and formatting
  - [ ] Configure mypy for type checking
- [ ] Create module structure
  - [ ] `nblite/__init__.py` - Public API
  - [ ] `nblite/core/__init__.py`
  - [ ] `nblite/config/__init__.py`
  - [ ] `nblite/export/__init__.py`
  - [ ] `nblite/sync/__init__.py`
  - [ ] `nblite/git/__init__.py`
  - [ ] `nblite/docs/__init__.py`
  - [ ] `nblite/extensions/__init__.py`
  - [ ] `nblite/cli/__init__.py`
  - [ ] `nblite/utils/__init__.py`
- [ ] Set up test infrastructure
  - [ ] `tests/conftest.py` with shared fixtures
  - [ ] `tests/fixtures/` directory for test notebooks

### Pytest Tests

```python
# tests/test_package.py

def test_package_imports():
    """Verify all main modules can be imported."""
    import nblite
    from nblite import core, config, export, git, docs, extensions, cli

def test_version_defined():
    """Verify package version is defined."""
    import nblite
    assert hasattr(nblite, '__version__')
    assert nblite.__version__

def test_notebookx_available():
    """Verify notebookx dependency is available."""
    import notebookx
    assert hasattr(notebookx, 'Notebook')
```

---

## Milestone 2: Directive System

### Tasks

- [ ] Implement `DirectiveDefinition` dataclass
  - [ ] `name`, `in_topmatter`, `value_parser`, `allows_inline`, `description`
- [ ] Implement directive registry
  - [ ] `register_directive(definition)`
  - [ ] `get_directive_definition(name)`
  - [ ] `list_directive_definitions()`
- [ ] Implement `Directive` dataclass
  - [ ] `cell`, `line_num`, `py_code`, `name`, `value`, `value_parsed`
- [ ] Implement directive parsing
  - [ ] Single line: `#|directive_name value`
  - [ ] Multi-line with continuation: `#|directive \`
  - [ ] Inline: `code #|directive_name`
  - [ ] Escaped backslash: `#|directive path\\to\\file`
- [ ] Register built-in directive definitions
  - [ ] `default_exp`, `export`, `exporti`, `export_to`
  - [ ] `export_as_func`, `set_func_signature`, `top_export`
  - [ ] `func_return`, `func_return_line`
  - [ ] `hide`, `hide_input`, `hide_output`
  - [ ] `eval`, `skip_evals`, `skip_evals_stop`
- [ ] Implement topmatter validation
  - [ ] Check if directive is in topmatter position
  - [ ] Raise error for topmatter-required directives not in topmatter

### Pytest Tests

```python
# tests/test_directive.py

import pytest
from nblite.core.directive import (
    Directive, DirectiveDefinition,
    register_directive, get_directive_definition,
    parse_directives_from_source
)


class TestDirectiveDefinition:
    def test_create_basic_definition(self):
        """Test creating a basic directive definition."""
        defn = DirectiveDefinition(name="export")
        assert defn.name == "export"
        assert defn.in_topmatter is True
        assert defn.value_parser is None
        assert defn.allows_inline is False

    def test_create_inline_definition(self):
        """Test creating a definition that allows inline."""
        defn = DirectiveDefinition(
            name="func_return_line",
            in_topmatter=False,
            allows_inline=True
        )
        assert defn.allows_inline is True
        assert defn.in_topmatter is False

    def test_definition_with_parser(self):
        """Test definition with custom value parser."""
        defn = DirectiveDefinition(
            name="test_dir",
            value_parser=lambda v: v.upper()
        )
        assert defn.value_parser("hello") == "HELLO"


class TestDirectiveRegistry:
    def test_register_and_retrieve(self):
        """Test registering and retrieving directives."""
        defn = DirectiveDefinition(name="test_directive")
        register_directive(defn)
        retrieved = get_directive_definition("test_directive")
        assert retrieved.name == "test_directive"

    def test_builtin_directives_registered(self):
        """Test that built-in directives are registered."""
        assert get_directive_definition("export") is not None
        assert get_directive_definition("default_exp") is not None
        assert get_directive_definition("func_return_line") is not None

    def test_unknown_directive_returns_none(self):
        """Test unknown directive returns None."""
        result = get_directive_definition("nonexistent_directive_xyz")
        assert result is None


class TestDirectiveParsing:
    def test_parse_simple_directive(self):
        """Test parsing a simple directive."""
        source = "#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "export"
        assert directives[0].value == ""

    def test_parse_directive_with_value(self):
        """Test parsing directive with value."""
        source = "#|default_exp utils.helpers"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "default_exp"
        assert directives[0].value == "utils.helpers"

    def test_parse_multiline_directive(self):
        """Test parsing multi-line directive with continuation."""
        source = "#|directive_name \\\n#   value1 \\\n#   value2"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert "value1" in directives[0].value
        assert "value2" in directives[0].value

    def test_parse_inline_directive(self):
        """Test parsing inline directive after code."""
        source = "x = 42 #|func_return_line"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert directives[0].name == "func_return_line"
        assert directives[0].py_code == "x = 42 "

    def test_parse_escaped_backslash(self):
        """Test parsing directive with escaped backslash."""
        source = "#|directive path\\\\to\\\\file"
        directives = parse_directives_from_source(source)
        assert len(directives) == 1
        assert "\\" in directives[0].value

    def test_parse_multiple_directives(self):
        """Test parsing multiple directives in one cell."""
        source = "#|default_exp utils\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert len(directives) == 2
        assert directives[0].name == "default_exp"
        assert directives[1].name == "export"

    def test_directive_line_numbers(self):
        """Test that directive line numbers are correct."""
        source = "#|default_exp utils\n\n#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        assert directives[0].line_num == 0
        assert directives[1].line_num == 2


class TestTopmatter:
    def test_topmatter_valid(self):
        """Test valid topmatter directive."""
        source = "#|export\ndef foo(): pass"
        directives = parse_directives_from_source(source)
        # Should not raise - directive is in topmatter
        assert directives[0].is_in_topmatter() is True

    def test_topmatter_after_code_invalid(self):
        """Test topmatter directive after code raises error."""
        source = "x = 1\n#|export\ndef foo(): pass"
        with pytest.raises(DirectiveError, match="must be in topmatter"):
            parse_directives_from_source(source, validate=True)

    def test_inline_directive_not_in_topmatter(self):
        """Test inline directive is not in topmatter."""
        source = "x = 42 #|func_return_line"
        directives = parse_directives_from_source(source)
        assert directives[0].is_in_topmatter() is False

    def test_inline_allowed_after_code(self):
        """Test inline directive allowed after code."""
        source = "def foo():\n    result #|func_return_line"
        # Should not raise - func_return_line allows inline
        directives = parse_directives_from_source(source, validate=True)
        assert len(directives) == 1
```

---

## Milestone 3: Cell & Notebook Classes

### Tasks

- [ ] Implement `Cell` wrapper class
  - [ ] `inner` - reference to notebookx cell
  - [ ] `directives` - dict of directives by name
  - [ ] `index` - cell index in notebook
  - [ ] `source` property
  - [ ] `source_without_directives` property
  - [ ] `is_code`, `is_markdown`, `is_raw` properties
  - [ ] `has_directive(name)` method
  - [ ] `get_directive(name)` method
- [ ] Implement `Notebook` class extending notebookx
  - [ ] `from_file(path, format)` classmethod
  - [ ] `from_notebookx(nb, source_path)` classmethod
  - [ ] `cells` property returning wrapped cells
  - [ ] `directives` property - all directives by name
  - [ ] `get_directive(name)` method
  - [ ] `get_directives(name)` method
  - [ ] `default_exp` property
  - [ ] `exported_cells` property
  - [ ] `source_path` attribute

### Pytest Tests

```python
# tests/test_cell.py

import pytest
from nblite.core.cell import Cell
from nblite.core.notebook import Notebook


class TestCell:
    @pytest.fixture
    def sample_code_cell(self, tmp_path):
        """Create a sample code cell."""
        nb_content = '''{"cells": [{"cell_type": "code", "source": "#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)
        return nb.cells[0]

    def test_cell_source(self, sample_code_cell):
        """Test cell source property."""
        assert "def foo():" in sample_code_cell.source

    def test_cell_source_without_directives(self, sample_code_cell):
        """Test source with directives removed."""
        source = sample_code_cell.source_without_directives
        assert "#|export" not in source
        assert "def foo():" in source

    def test_cell_is_code(self, sample_code_cell):
        """Test is_code property."""
        assert sample_code_cell.is_code is True
        assert sample_code_cell.is_markdown is False

    def test_cell_has_directive(self, sample_code_cell):
        """Test has_directive method."""
        assert sample_code_cell.has_directive("export") is True
        assert sample_code_cell.has_directive("hide") is False

    def test_cell_get_directive(self, sample_code_cell):
        """Test get_directive method."""
        directive = sample_code_cell.get_directive("export")
        assert directive is not None
        assert directive.name == "export"

    def test_cell_directives_dict(self, sample_code_cell):
        """Test directives dictionary."""
        assert "export" in sample_code_cell.directives
        assert len(sample_code_cell.directives["export"]) == 1


# tests/test_notebook.py

class TestNotebook:
    @pytest.fixture
    def sample_notebook(self, tmp_path):
        """Create a sample notebook with multiple cells."""
        nb_content = '''{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp utils", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|export\\ndef foo(): pass", "metadata": {}, "outputs": []},
                {"cell_type": "markdown", "source": "# Documentation", "metadata": {}},
                {"cell_type": "code", "source": "#|export\\ndef bar(): pass", "metadata": {}, "outputs": []}
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        nb_path = tmp_path / "utils.ipynb"
        nb_path.write_text(nb_content)
        return Notebook.from_file(nb_path)

    def test_notebook_from_file(self, sample_notebook):
        """Test loading notebook from file."""
        assert sample_notebook is not None
        assert len(sample_notebook.cells) == 4

    def test_notebook_default_exp(self, sample_notebook):
        """Test default_exp property."""
        assert sample_notebook.default_exp == "utils"

    def test_notebook_exported_cells(self, sample_notebook):
        """Test exported_cells property."""
        exported = sample_notebook.exported_cells
        assert len(exported) == 2
        assert all(c.has_directive("export") for c in exported)

    def test_notebook_directives(self, sample_notebook):
        """Test all directives property."""
        directives = sample_notebook.directives
        assert "default_exp" in directives
        assert "export" in directives
        assert len(directives["export"]) == 2

    def test_notebook_get_directive(self, sample_notebook):
        """Test get_directive for single directive."""
        directive = sample_notebook.get_directive("default_exp")
        assert directive.value == "utils"

    def test_notebook_get_directives(self, sample_notebook):
        """Test get_directives for multiple directives."""
        directives = sample_notebook.get_directives("export")
        assert len(directives) == 2

    def test_notebook_source_path(self, sample_notebook, tmp_path):
        """Test source_path attribute."""
        assert sample_notebook.source_path == tmp_path / "utils.ipynb"

    def test_notebook_cell_indices(self, sample_notebook):
        """Test that cell indices are correct."""
        for i, cell in enumerate(sample_notebook.cells):
            assert cell.index == i

    def test_notebook_from_pct_file(self, tmp_path):
        """Test loading notebook from percent format."""
        pct_content = "# %% [markdown]\\n# Title\\n\\n# %%\\n#|export\\ndef foo(): pass"
        pct_path = tmp_path / "test.pct.py"
        pct_path.write_text(pct_content)
        nb = Notebook.from_file(pct_path)
        assert len(nb.cells) == 2


class TestNotebookWithoutDefaultExp:
    def test_notebook_no_default_exp(self, tmp_path):
        """Test notebook without default_exp directive."""
        nb_content = '''{"cells": [{"cell_type": "code", "source": "#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)
        assert nb.default_exp is None
```

---

## Milestone 4: Configuration System

### Tasks

- [ ] Implement Pydantic models
  - [ ] `ExportRule` - from_key, to_key
  - [ ] `CodeLocationConfig` - path, format, export_mode
  - [ ] `TemplatesConfig` - folder, default
  - [ ] `ExtensionEntry` - path OR module validation
  - [ ] `ExportConfig` - include_autogenerated_warning, cell_reference_style
  - [ ] `GitConfig` - auto_clean, auto_export, validate_staging
  - [ ] `CleanConfig` - options for nbl clean
  - [ ] `NbliteConfig` - top-level config model
- [ ] Implement config loader
  - [ ] `load_config(path)` - load from nblite.toml
  - [ ] `find_config_file(start_path)` - search upward
  - [ ] `parse_export_pipeline(pipeline_str)` - parse pipeline string
- [ ] Implement config validation
  - [ ] Validate code location references in pipeline
  - [ ] Validate docs_cl exists
  - [ ] Validate extension paths/modules

### Pytest Tests

```python
# tests/test_config.py

import pytest
from pathlib import Path
from nblite.config.schema import (
    NbliteConfig, CodeLocationConfig, ExportRule,
    ExtensionEntry, ExportConfig, GitConfig
)
from nblite.config.loader import load_config, find_config_file, parse_export_pipeline


class TestExportRule:
    def test_create_export_rule(self):
        """Test creating an export rule."""
        rule = ExportRule(from_key="nbs", to_key="pts")
        assert rule.from_key == "nbs"
        assert rule.to_key == "pts"


class TestCodeLocationConfig:
    def test_create_code_location(self):
        """Test creating a code location config."""
        cl = CodeLocationConfig(
            path="mypackage",
            format="module",
            export_mode="percent"
        )
        assert cl.path == "mypackage"
        assert cl.format == "module"

    def test_invalid_format(self):
        """Test invalid format raises error."""
        with pytest.raises(ValueError):
            CodeLocationConfig(path="pkg", format="invalid")


class TestExtensionEntry:
    def test_extension_with_path(self):
        """Test extension entry with file path."""
        ext = ExtensionEntry(path="nblite_ext.py")
        assert ext.path == "nblite_ext.py"
        assert ext.module is None

    def test_extension_with_module(self):
        """Test extension entry with module path."""
        ext = ExtensionEntry(module="mypackage.extension")
        assert ext.module == "mypackage.extension"
        assert ext.path is None

    def test_extension_neither_raises(self):
        """Test neither path nor module raises error."""
        with pytest.raises(ValueError, match="Either 'path' or 'module'"):
            ExtensionEntry()

    def test_extension_both_raises(self):
        """Test both path and module raises error."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            ExtensionEntry(path="ext.py", module="pkg.ext")


class TestNbliteConfig:
    def test_minimal_config(self):
        """Test minimal valid config."""
        config = NbliteConfig(
            export_pipeline=[ExportRule(from_key="nbs", to_key="lib")],
            code_locations={
                "nbs": CodeLocationConfig(path="nbs", format="ipynb"),
                "lib": CodeLocationConfig(path="mypackage", format="module")
            }
        )
        assert len(config.export_pipeline) == 1
        assert len(config.code_locations) == 2

    def test_config_defaults(self):
        """Test config defaults are applied."""
        config = NbliteConfig(
            export_pipeline=[],
            code_locations={}
        )
        assert config.docs_generator == "jupyterbook"
        assert config.export.include_autogenerated_warning is True
        assert config.git.auto_clean is True

    def test_config_with_extensions(self):
        """Test config with multiple extensions."""
        config = NbliteConfig(
            export_pipeline=[],
            code_locations={},
            extensions=[
                ExtensionEntry(path="ext1.py"),
                ExtensionEntry(module="pkg.ext2")
            ]
        )
        assert len(config.extensions) == 2


class TestParseExportPipeline:
    def test_parse_simple_pipeline(self):
        """Test parsing simple pipeline string."""
        pipeline_str = "nbs -> pts"
        rules = parse_export_pipeline(pipeline_str)
        assert len(rules) == 1
        assert rules[0].from_key == "nbs"
        assert rules[0].to_key == "pts"

    def test_parse_multiline_pipeline(self):
        """Test parsing multi-line pipeline."""
        pipeline_str = """
        nbs -> pts
        pts -> lib
        """
        rules = parse_export_pipeline(pipeline_str)
        assert len(rules) == 2
        assert rules[0].from_key == "nbs"
        assert rules[1].to_key == "lib"

    def test_parse_empty_pipeline(self):
        """Test parsing empty pipeline."""
        rules = parse_export_pipeline("")
        assert len(rules) == 0


class TestConfigLoader:
    def test_load_config_from_file(self, tmp_path):
        """Test loading config from TOML file."""
        config_content = '''
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mypackage"
format = "module"
'''
        config_path = tmp_path / "nblite.toml"
        config_path.write_text(config_content)
        config = load_config(config_path)
        assert config is not None
        assert len(config.export_pipeline) == 1

    def test_find_config_file(self, tmp_path):
        """Test finding config file by searching upward."""
        # Create nested directory structure
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        config_path = tmp_path / "nblite.toml"
        config_path.write_text('export_pipeline = ""')

        found = find_config_file(nested)
        assert found == config_path

    def test_find_config_file_not_found(self, tmp_path):
        """Test config file not found returns None."""
        found = find_config_file(tmp_path)
        assert found is None

    def test_load_config_validates_code_locations(self, tmp_path):
        """Test that config validates pipeline references."""
        config_content = '''
export_pipeline = "nbs -> nonexistent"

[cl.nbs]
path = "nbs"
format = "ipynb"
'''
        config_path = tmp_path / "nblite.toml"
        config_path.write_text(config_content)
        with pytest.raises(ValueError, match="nonexistent"):
            load_config(config_path)
```

---

## Milestone 5: Code Location & PyFile Classes

### Tasks

- [ ] Implement `CodeLocation` dataclass
  - [ ] `key`, `path`, `format`, `export_mode`
  - [ ] `file_ext` property
  - [ ] `is_notebook` property
  - [ ] `get_files(ignore_dunders, ignore_hidden)` method
- [ ] Implement `PyFile` class
  - [ ] `from_file(path)` classmethod
  - [ ] `path`, `content`, `is_autogenerated` attributes
  - [ ] `source_notebook` property (parse from header)
  - [ ] `cells` property (for percent-style files)
  - [ ] `module_path` property

### Pytest Tests

```python
# tests/test_code_location.py

import pytest
from pathlib import Path
from nblite.core.code_location import CodeLocation
from nblite.config.schema import ExportMode


class TestCodeLocation:
    def test_create_ipynb_location(self, tmp_path):
        """Test creating ipynb code location."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        cl = CodeLocation(
            key="nbs",
            path=nbs_dir,
            format="ipynb",
            export_mode=ExportMode.PERCENT
        )
        assert cl.file_ext == ".ipynb"
        assert cl.is_notebook is True

    def test_create_percent_location(self, tmp_path):
        """Test creating percent code location."""
        pts_dir = tmp_path / "pts"
        pts_dir.mkdir()
        cl = CodeLocation(
            key="pts",
            path=pts_dir,
            format="percent",
            export_mode=ExportMode.PERCENT
        )
        assert cl.file_ext == ".pct.py"
        assert cl.is_notebook is True

    def test_create_module_location(self, tmp_path):
        """Test creating module code location."""
        lib_dir = tmp_path / "mypackage"
        lib_dir.mkdir()
        cl = CodeLocation(
            key="lib",
            path=lib_dir,
            format="module",
            export_mode=ExportMode.PERCENT
        )
        assert cl.file_ext == ".py"
        assert cl.is_notebook is False

    def test_get_files(self, tmp_path):
        """Test getting files from code location."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        (nbs_dir / "utils.ipynb").write_text("{}")
        (nbs_dir / "api.ipynb").write_text("{}")
        (nbs_dir / "__init__.ipynb").write_text("{}")
        (nbs_dir / ".hidden.ipynb").write_text("{}")

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb", export_mode=ExportMode.PERCENT)
        files = cl.get_files()

        assert len(files) == 2
        assert all(not f.name.startswith("__") for f in files)
        assert all(not f.name.startswith(".") for f in files)

    def test_get_files_include_dunders(self, tmp_path):
        """Test getting files including dunder files."""
        nbs_dir = tmp_path / "nbs"
        nbs_dir.mkdir()
        (nbs_dir / "utils.ipynb").write_text("{}")
        (nbs_dir / "__init__.ipynb").write_text("{}")

        cl = CodeLocation(key="nbs", path=nbs_dir, format="ipynb", export_mode=ExportMode.PERCENT)
        files = cl.get_files(ignore_dunders=False)

        assert len(files) == 2


# tests/test_pyfile.py

class TestPyFile:
    def test_load_autogenerated_file(self, tmp_path):
        """Test loading autogenerated Python file."""
        content = '''# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/utils.ipynb

# %% ../nbs/utils.ipynb 0
def foo():
    pass
'''
        py_path = tmp_path / "utils.py"
        py_path.write_text(content)

        from nblite.core.pyfile import PyFile
        pyfile = PyFile.from_file(py_path)

        assert pyfile.is_autogenerated is True
        assert pyfile.source_notebook == Path("../nbs/utils.ipynb")

    def test_load_regular_file(self, tmp_path):
        """Test loading non-autogenerated Python file."""
        content = "def foo(): pass"
        py_path = tmp_path / "manual.py"
        py_path.write_text(content)

        from nblite.core.pyfile import PyFile
        pyfile = PyFile.from_file(py_path)

        assert pyfile.is_autogenerated is False
        assert pyfile.source_notebook is None

    def test_parse_percent_cells(self, tmp_path):
        """Test parsing cells from percent-style file."""
        content = '''# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/utils.ipynb

# %% ../nbs/utils.ipynb 0
def foo():
    pass

# %% ../nbs/utils.ipynb 2
def bar():
    pass
'''
        py_path = tmp_path / "utils.py"
        py_path.write_text(content)

        from nblite.core.pyfile import PyFile
        pyfile = PyFile.from_file(py_path)

        assert len(pyfile.cells) == 2
        assert pyfile.cells[0].source_cell_index == 0
        assert pyfile.cells[1].source_cell_index == 2

    def test_module_path(self, tmp_path):
        """Test module path calculation."""
        pkg_dir = tmp_path / "mypackage" / "utils"
        pkg_dir.mkdir(parents=True)
        py_path = pkg_dir / "helpers.py"
        py_path.write_text("def foo(): pass")

        from nblite.core.pyfile import PyFile
        pyfile = PyFile.from_file(py_path)
        pyfile._package_root = tmp_path / "mypackage"

        assert pyfile.module_path == "mypackage.utils.helpers"
```

---

## Milestone 6: Basic Export Pipeline

### Tasks

- [ ] Implement notebook → notebook export (ipynb → pct.py)
  - [ ] Preserve all cells
  - [ ] Use notebookx for format conversion
- [ ] Implement notebook → module export
  - [ ] Collect cells with `#|export`, `#|exporti`, `#|export_to`
  - [ ] Generate `__all__` list
  - [ ] Remove directive lines from source
  - [ ] Handle `export_mode=percent` (with cell markers)
  - [ ] Handle `export_mode=py` (plain Python)
  - [ ] Add autogenerated header
- [ ] Implement export pipeline orchestration
  - [ ] Parse pipeline rules
  - [ ] Execute rules in order
  - [ ] Handle specific notebook filtering

### Pytest Tests

```python
# tests/test_export.py

import pytest
from pathlib import Path
from nblite.export.pipeline import export_notebook_to_notebook, export_notebook_to_module
from nblite.export.modes import ExportMode
from nblite.core.notebook import Notebook


class TestNotebookToNotebook:
    def test_ipynb_to_percent(self, tmp_path):
        """Test converting ipynb to percent format."""
        nb_content = '''{"cells": [{"cell_type": "code", "source": "#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        pct_path = tmp_path / "test.pct.py"

        nb = Notebook.from_file(ipynb_path)
        export_notebook_to_notebook(nb, pct_path, format="percent")

        assert pct_path.exists()
        content = pct_path.read_text()
        assert "# %%" in content
        assert "def foo():" in content

    def test_percent_to_ipynb(self, tmp_path):
        """Test converting percent to ipynb format."""
        pct_content = "# %%\\n#|export\\ndef foo(): pass"
        pct_path = tmp_path / "test.pct.py"
        pct_path.write_text(pct_content)
        ipynb_path = tmp_path / "test.ipynb"

        nb = Notebook.from_file(pct_path)
        export_notebook_to_notebook(nb, ipynb_path, format="ipynb")

        assert ipynb_path.exists()
        import json
        data = json.loads(ipynb_path.read_text())
        assert "cells" in data


class TestNotebookToModule:
    @pytest.fixture
    def notebook_with_exports(self, tmp_path):
        """Create notebook with export directives."""
        nb_content = '''{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp utils", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|export\\ndef foo():\\n    pass", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "# Not exported\\ntest_var = 1", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|export\\ndef bar():\\n    return 42", "metadata": {}, "outputs": []}
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        nb_path = tmp_path / "utils.ipynb"
        nb_path.write_text(nb_content)
        return Notebook.from_file(nb_path)

    def test_export_percent_mode(self, notebook_with_exports, tmp_path):
        """Test export with percent mode."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            export_mode=ExportMode.PERCENT
        )

        content = module_path.read_text()
        assert "AUTOGENERATED" in content
        assert "# %%" in content
        assert "def foo():" in content
        assert "def bar():" in content
        assert "#|export" not in content
        assert "test_var" not in content

    def test_export_py_mode(self, notebook_with_exports, tmp_path):
        """Test export with py mode (no cell markers)."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            export_mode=ExportMode.PY
        )

        content = module_path.read_text()
        assert "AUTOGENERATED" in content
        assert "# %%" not in content
        assert "def foo():" in content

    def test_export_generates_all(self, notebook_with_exports, tmp_path):
        """Test that __all__ is generated."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            export_mode=ExportMode.PERCENT
        )

        content = module_path.read_text()
        assert "__all__" in content
        assert "'foo'" in content or '"foo"' in content
        assert "'bar'" in content or '"bar"' in content

    def test_export_removes_directives(self, notebook_with_exports, tmp_path):
        """Test that directive lines are removed."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            export_mode=ExportMode.PERCENT
        )

        content = module_path.read_text()
        assert "#|export" not in content
        assert "#|default_exp" not in content

    def test_export_without_warning(self, notebook_with_exports, tmp_path):
        """Test export without autogenerated warning."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            export_mode=ExportMode.PERCENT,
            include_warning=False
        )

        content = module_path.read_text()
        assert "AUTOGENERATED" not in content


class TestExportPipeline:
    def test_run_pipeline(self, tmp_path):
        """Test running full export pipeline."""
        from nblite.export.pipeline import run_pipeline
        from nblite.core.project import NbliteProject

        # Create project structure
        (tmp_path / "nbs").mkdir()
        (tmp_path / "mypackage").mkdir()

        nb_content = '''{"cells": [{"cell_type": "code", "source": "#|default_exp utils\\n#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        (tmp_path / "nbs" / "utils.ipynb").write_text(nb_content)

        config_content = '''
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mypackage"
format = "module"
'''
        (tmp_path / "nblite.toml").write_text(config_content)

        project = NbliteProject.from_path(tmp_path)
        result = run_pipeline(project)

        assert result.success
        assert (tmp_path / "mypackage" / "utils.py").exists()
```

---

## Milestone 7: NbliteProject Class

### Tasks

- [ ] Implement `NbliteProject` class
  - [ ] `from_path(path)` classmethod
  - [ ] `find_project_root(start_path)` classmethod
  - [ ] `root_path`, `config` attributes
  - [ ] `code_locations` property
  - [ ] `get_code_location(key)` method
  - [ ] `get_notebooks(code_location)` method
  - [ ] `notebooks` property (all loaded notebooks)
  - [ ] `py_files` property (all loaded Python files)
- [ ] Implement twin tracking
  - [ ] `get_notebook_twins(notebook)` method
  - [ ] Calculate twin paths based on pipeline
- [ ] Implement lineage tracking
  - [ ] `NotebookLineage` dataclass
  - [ ] `get_notebook_lineage(notebook)` method
- [ ] Implement project-level methods
  - [ ] `export(pipeline, notebooks, hooks)` method
  - [ ] `clean(notebooks, options)` method
  - [ ] `validate_staging()` method

### Pytest Tests

```python
# tests/test_project.py

import pytest
from pathlib import Path
from nblite.core.project import NbliteProject
from nblite.sync.lineage import NotebookLineage


@pytest.fixture
def sample_project(tmp_path):
    """Create a complete sample project."""
    # Create directories
    (tmp_path / "nbs").mkdir()
    (tmp_path / "pts").mkdir()
    (tmp_path / "mypackage").mkdir()

    # Create notebooks
    nb_content = '''{"cells": [{"cell_type": "code", "source": "#|default_exp utils\\n#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
    (tmp_path / "nbs" / "utils.ipynb").write_text(nb_content)

    # Create config
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


class TestNbliteProject:
    def test_from_path(self, sample_project):
        """Test loading project from path."""
        project = NbliteProject.from_path(sample_project)
        assert project.root_path == sample_project
        assert project.config is not None

    def test_find_project_root(self, sample_project):
        """Test finding project root from nested path."""
        nested = sample_project / "nbs" / "subfolder"
        nested.mkdir(parents=True)

        root = NbliteProject.find_project_root(nested)
        assert root == sample_project

    def test_code_locations(self, sample_project):
        """Test accessing code locations."""
        project = NbliteProject.from_path(sample_project)

        assert "nbs" in project.code_locations
        assert "pts" in project.code_locations
        assert "lib" in project.code_locations

    def test_get_code_location(self, sample_project):
        """Test getting specific code location."""
        project = NbliteProject.from_path(sample_project)

        nbs_cl = project.get_code_location("nbs")
        assert nbs_cl.format == "ipynb"

    def test_get_notebooks(self, sample_project):
        """Test getting notebooks from project."""
        project = NbliteProject.from_path(sample_project)

        notebooks = project.get_notebooks()
        assert len(notebooks) == 1
        assert notebooks[0].default_exp == "utils"

    def test_get_notebooks_by_location(self, sample_project):
        """Test getting notebooks filtered by code location."""
        project = NbliteProject.from_path(sample_project)

        nbs_notebooks = project.get_notebooks(code_location="nbs")
        assert len(nbs_notebooks) == 1


class TestTwinTracking:
    def test_get_notebook_twins(self, sample_project):
        """Test getting twin paths for a notebook."""
        project = NbliteProject.from_path(sample_project)
        notebooks = project.get_notebooks()

        twins = project.get_notebook_twins(notebooks[0])

        assert len(twins) >= 1
        # Should include the pct.py path
        assert any("pts" in str(t) for t in twins)


class TestLineageTracking:
    def test_get_notebook_lineage(self, sample_project):
        """Test getting full lineage for a notebook."""
        # First run export to create files
        project = NbliteProject.from_path(sample_project)
        project.export()

        notebooks = project.get_notebooks()
        lineage = project.get_notebook_lineage(notebooks[0])

        assert isinstance(lineage, NotebookLineage)
        assert lineage.source == notebooks[0].source_path
        assert "pts" in lineage.twins
        assert lineage.module_path is not None


class TestProjectExport:
    def test_export_all(self, sample_project):
        """Test exporting all notebooks."""
        project = NbliteProject.from_path(sample_project)
        result = project.export()

        assert result.success
        assert (sample_project / "pts" / "utils.pct.py").exists()
        assert (sample_project / "mypackage" / "utils.py").exists()

    def test_export_specific_notebooks(self, sample_project):
        """Test exporting specific notebooks."""
        project = NbliteProject.from_path(sample_project)
        nb_path = sample_project / "nbs" / "utils.ipynb"

        result = project.export(notebooks=[nb_path])
        assert result.success


class TestProjectClean:
    def test_clean_notebooks(self, sample_project):
        """Test cleaning notebooks."""
        # Add output to notebook
        nb_path = sample_project / "nbs" / "utils.ipynb"
        nb_content = '''{"cells": [{"cell_type": "code", "source": "#|export\\ndef foo(): pass", "metadata": {}, "outputs": [{"output_type": "stream", "text": "hello"}], "execution_count": 1}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        nb_path.write_text(nb_content)

        project = NbliteProject.from_path(sample_project)
        project.clean()

        import json
        cleaned = json.loads(nb_path.read_text())
        assert cleaned["cells"][0]["outputs"] == []
```

---

## Milestone 8: CLI Foundation

### Tasks

- [ ] Set up typer app with lazy imports
  - [ ] Main app in `cli/app.py`
  - [ ] Command modules in `cli/commands/`
- [ ] Implement core commands
  - [ ] `nbl init` - Initialize project
  - [ ] `nbl new` - Create new notebook
  - [ ] `nbl export` - Run export pipeline
  - [ ] `nbl clean` - Clean notebooks (wraps nbx)
  - [ ] `nbl convert` - Convert formats (wraps nbx)
  - [ ] `nbl info` - Show project info
  - [ ] `nbl list` - List notebooks/files

### Pytest Tests

```python
# tests/test_cli.py

import pytest
from typer.testing import CliRunner
from nblite.cli.app import app


runner = CliRunner()


class TestCLIBasics:
    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "nblite" in result.output.lower() or "0." in result.output

    def test_help(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "export" in result.output
        assert "clean" in result.output


class TestInitCommand:
    def test_init_creates_config(self, tmp_path):
        """Test nbl init creates nblite.toml."""
        result = runner.invoke(app, ["init"], input="\\n\\n\\n")
        # Note: test may need to be run from tmp_path
        assert result.exit_code == 0

    def test_init_with_name(self, tmp_path):
        """Test nbl init with --name option."""
        import os
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--name", "mypackage", "--use-defaults"])
        assert result.exit_code == 0
        assert (tmp_path / "nblite.toml").exists()


class TestNewCommand:
    def test_new_creates_notebook(self, sample_project):
        """Test nbl new creates a notebook."""
        import os
        os.chdir(sample_project)
        result = runner.invoke(app, ["new", "nbs/api.ipynb", "-n", "api"])

        assert result.exit_code == 0
        assert (sample_project / "nbs" / "api.ipynb").exists()

    def test_new_with_template(self, sample_project):
        """Test nbl new with template."""
        import os
        os.chdir(sample_project)
        # First create a template
        templates_dir = sample_project / "templates"
        templates_dir.mkdir()
        (templates_dir / "api.pct.py").write_text("# %% \\n#|default_exp {{module_name}}")

        result = runner.invoke(app, ["new", "nbs/test.ipynb", "--template", "api"])
        assert result.exit_code == 0


class TestExportCommand:
    def test_export_runs(self, sample_project):
        """Test nbl export runs successfully."""
        import os
        os.chdir(sample_project)
        result = runner.invoke(app, ["export"])

        assert result.exit_code == 0
        assert (sample_project / "mypackage" / "utils.py").exists()

    def test_export_dry_run(self, sample_project):
        """Test nbl export --dry-run."""
        import os
        os.chdir(sample_project)
        result = runner.invoke(app, ["export", "--dry-run"])

        assert result.exit_code == 0
        # Dry run should not create files
        assert not (sample_project / "mypackage" / "utils.py").exists()


class TestCleanCommand:
    def test_clean_wraps_nbx(self, sample_project):
        """Test nbl clean wraps nbx clean."""
        import os
        os.chdir(sample_project)
        result = runner.invoke(app, ["clean"])

        assert result.exit_code == 0


class TestConvertCommand:
    def test_convert_ipynb_to_pct(self, tmp_path):
        """Test nbl convert from ipynb to pct."""
        nb_content = '''{"cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        pct_path = tmp_path / "test.pct.py"

        result = runner.invoke(app, ["convert", str(ipynb_path), str(pct_path)])

        assert result.exit_code == 0
        assert pct_path.exists()


class TestInfoCommand:
    def test_info_shows_project(self, sample_project):
        """Test nbl info shows project information."""
        import os
        os.chdir(sample_project)
        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "nbs" in result.output
        assert "lib" in result.output


class TestListCommand:
    def test_list_notebooks(self, sample_project):
        """Test nbl list shows notebooks."""
        import os
        os.chdir(sample_project)
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "utils.ipynb" in result.output
```

---

## Milestone 9: Git Integration

### Tasks

- [ ] Implement staging validation
  - [ ] Check notebooks are clean
  - [ ] Check twins are staged together
  - [ ] `nbl git validate` command
- [ ] Implement hook installation
  - [ ] Support projects in subdirectories
  - [ ] Add to existing hooks (don't overwrite)
  - [ ] Use markers for clean uninstall
  - [ ] `nbl install-hooks` command
  - [ ] `nbl uninstall-hooks` command
- [ ] Implement `nbl git add` command
  - [ ] Export and clean before staging
  - [ ] Stage twins together

### Pytest Tests

```python
# tests/test_git.py

import pytest
import subprocess
from pathlib import Path
from nblite.git.hooks import install_hooks, uninstall_hooks
from nblite.git.staging import validate_staging
from nblite.core.project import NbliteProject


@pytest.fixture
def git_project(tmp_path):
    """Create a project with git initialized."""
    # Initialize git
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path)

    # Create project structure
    (tmp_path / "nbs").mkdir()
    (tmp_path / "mypackage").mkdir()

    nb_content = '''{"cells": [{"cell_type": "code", "source": "#|default_exp utils\\n#|export\\ndef foo(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
    (tmp_path / "nbs" / "utils.ipynb").write_text(nb_content)

    config_content = '''
export_pipeline = "nbs -> lib"

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mypackage"
format = "module"
'''
    (tmp_path / "nblite.toml").write_text(config_content)

    return tmp_path


class TestHookInstallation:
    def test_install_hooks(self, git_project):
        """Test installing git hooks."""
        project = NbliteProject.from_path(git_project)
        install_hooks(project)

        hook_path = git_project / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        content = hook_path.read_text()
        assert "NBLITE HOOK" in content

    def test_install_hooks_preserves_existing(self, git_project):
        """Test that existing hook content is preserved."""
        hook_dir = git_project / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hook_dir / "pre-commit"
        hook_path.write_text("#!/bin/sh\\necho 'existing hook'\\n")
        hook_path.chmod(0o755)

        project = NbliteProject.from_path(git_project)
        install_hooks(project)

        content = hook_path.read_text()
        assert "existing hook" in content
        assert "NBLITE HOOK" in content

    def test_uninstall_hooks(self, git_project):
        """Test uninstalling git hooks."""
        project = NbliteProject.from_path(git_project)
        install_hooks(project)
        uninstall_hooks(project)

        hook_path = git_project / ".git" / "hooks" / "pre-commit"
        if hook_path.exists():
            content = hook_path.read_text()
            assert "NBLITE HOOK" not in content

    def test_install_hooks_subdirectory(self, tmp_path):
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


class TestStagingValidation:
    def test_validate_clean_notebook(self, git_project):
        """Test validation passes for clean notebook."""
        project = NbliteProject.from_path(git_project)

        # Stage clean notebook
        subprocess.run(["git", "add", "nbs/utils.ipynb"], cwd=git_project)

        result = validate_staging(project)
        assert result.valid

    def test_validate_unclean_notebook_fails(self, git_project):
        """Test validation fails for unclean notebook."""
        # Add outputs to notebook
        nb_path = git_project / "nbs" / "utils.ipynb"
        nb_content = '''{"cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": [{"output_type": "stream", "text": "1"}], "execution_count": 1}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        nb_path.write_text(nb_content)

        project = NbliteProject.from_path(git_project)
        subprocess.run(["git", "add", "nbs/utils.ipynb"], cwd=git_project)

        result = validate_staging(project)
        assert not result.valid
        assert len(result.unclean_notebooks) > 0

    def test_validate_missing_twins(self, git_project):
        """Test validation warns about missing twins."""
        project = NbliteProject.from_path(git_project)

        # Export to create twins
        project.export()

        # Stage only the notebook, not the module
        subprocess.run(["git", "add", "nbs/utils.ipynb"], cwd=git_project)

        result = validate_staging(project)
        assert len(result.unstaged_twins) > 0
```

---

## Milestone 10: Extension System

### Tasks

- [ ] Implement `HookType` enum
  - [ ] PRE_EXPORT, POST_EXPORT
  - [ ] PRE_NOTEBOOK_EXPORT, POST_NOTEBOOK_EXPORT
  - [ ] PRE_CELL_EXPORT, POST_CELL_EXPORT
  - [ ] PRE_CLEAN, POST_CLEAN
  - [ ] DIRECTIVE_PARSED
- [ ] Implement `HookRegistry` class
  - [ ] `register(hook_type, callback)`
  - [ ] `trigger(hook_type, **context)`
  - [ ] `clear()`
- [ ] Implement `@hook` decorator
- [ ] Implement extension loading
  - [ ] Load from file path
  - [ ] Load from Python import path
  - [ ] Load multiple extensions
- [ ] Add CLI extension support
  - [ ] `--extension` flag on relevant commands

### Pytest Tests

```python
# tests/test_extensions.py

import pytest
from nblite.extensions.hooks import HookType, HookRegistry, hook
from nblite.extensions.loader import load_extension


class TestHookRegistry:
    def setup_method(self):
        """Clear registry before each test."""
        HookRegistry.clear()

    def test_register_hook(self):
        """Test registering a hook callback."""
        called = []

        def my_hook(**kwargs):
            called.append(True)

        HookRegistry.register(HookType.PRE_EXPORT, my_hook)
        HookRegistry.trigger(HookType.PRE_EXPORT)

        assert len(called) == 1

    def test_hook_decorator(self):
        """Test @hook decorator."""
        called = []

        @hook(HookType.POST_EXPORT)
        def after_export(**kwargs):
            called.append(True)

        HookRegistry.trigger(HookType.POST_EXPORT)

        assert len(called) == 1

    def test_hook_receives_context(self):
        """Test that hook receives context kwargs."""
        received = {}

        @hook(HookType.PRE_NOTEBOOK_EXPORT)
        def before_nb(**kwargs):
            received.update(kwargs)

        HookRegistry.trigger(HookType.PRE_NOTEBOOK_EXPORT, notebook="test", path="/test")

        assert received["notebook"] == "test"
        assert received["path"] == "/test"

    def test_multiple_hooks_same_type(self):
        """Test multiple hooks for same type."""
        results = []

        @hook(HookType.PRE_EXPORT)
        def hook1(**kwargs):
            results.append(1)

        @hook(HookType.PRE_EXPORT)
        def hook2(**kwargs):
            results.append(2)

        HookRegistry.trigger(HookType.PRE_EXPORT)

        assert results == [1, 2]

    def test_clear_hooks(self):
        """Test clearing all hooks."""
        called = []

        @hook(HookType.PRE_EXPORT)
        def my_hook(**kwargs):
            called.append(True)

        HookRegistry.clear()
        HookRegistry.trigger(HookType.PRE_EXPORT)

        assert len(called) == 0


class TestExtensionLoader:
    def test_load_from_file(self, tmp_path):
        """Test loading extension from file path."""
        ext_content = '''
from nblite.extensions import hook, HookType

LOADED = True

@hook(HookType.PRE_EXPORT)
def my_hook(**kwargs):
    pass
'''
        ext_path = tmp_path / "my_extension.py"
        ext_path.write_text(ext_content)

        HookRegistry.clear()
        load_extension(path=str(ext_path))

        # Verify hook was registered
        assert len(HookRegistry._hooks.get(HookType.PRE_EXPORT, [])) == 1

    def test_load_from_module(self):
        """Test loading extension from Python module."""
        # This test requires a real installed module
        # For unit testing, we can mock or skip
        pass

    def test_load_multiple_extensions(self, tmp_path):
        """Test loading multiple extensions."""
        ext1 = tmp_path / "ext1.py"
        ext1.write_text('''
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def hook1(**kwargs): pass
''')

        ext2 = tmp_path / "ext2.py"
        ext2.write_text('''
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def hook2(**kwargs): pass
''')

        HookRegistry.clear()
        load_extension(path=str(ext1))
        load_extension(path=str(ext2))

        assert len(HookRegistry._hooks.get(HookType.PRE_EXPORT, [])) == 2


class TestExtensionIntegration:
    def test_export_with_extension(self, sample_project, tmp_path):
        """Test export with extension hooks."""
        ext_content = '''
from nblite.extensions import hook, HookType

export_count = 0

@hook(HookType.PRE_NOTEBOOK_EXPORT)
def count_exports(**kwargs):
    global export_count
    export_count += 1
'''
        ext_path = sample_project / "my_ext.py"
        ext_path.write_text(ext_content)

        from nblite.core.project import NbliteProject
        HookRegistry.clear()
        load_extension(path=str(ext_path))

        project = NbliteProject.from_path(sample_project)
        project.export()

        # Hook should have been called
        # (verification depends on implementation)
```

---

## Milestone 11: Documentation Generation

### Tasks

- [ ] Implement `DocsGenerator` protocol
  - [ ] `prepare(project, output_dir)`
  - [ ] `build(output_dir, final_dir)`
  - [ ] `preview(output_dir)`
- [ ] Implement Jupyter Book generator
  - [ ] Generate `_toc.yml`
  - [ ] Generate `_config.yml`
  - [ ] Copy/link notebooks
  - [ ] Run `jupyter-book build`
- [ ] Implement MkDocs generator
  - [ ] Generate `mkdocs.yml`
  - [ ] Copy notebooks
  - [ ] Run `mkdocs build`
- [ ] Implement CLI commands
  - [ ] `nbl docs build`
  - [ ] `nbl docs preview`
  - [ ] `nbl docs readme`

### Pytest Tests

```python
# tests/test_docs.py

import pytest
from pathlib import Path
from nblite.docs.generator import get_generator
from nblite.docs.jupyterbook import JupyterBookGenerator
from nblite.docs.mkdocs import MkDocsGenerator


class TestDocsGenerator:
    def test_get_jupyterbook_generator(self):
        """Test getting Jupyter Book generator."""
        gen = get_generator("jupyterbook")
        assert isinstance(gen, JupyterBookGenerator)

    def test_get_mkdocs_generator(self):
        """Test getting MkDocs generator."""
        gen = get_generator("mkdocs")
        assert isinstance(gen, MkDocsGenerator)

    def test_unknown_generator_raises(self):
        """Test unknown generator raises error."""
        with pytest.raises(ValueError):
            get_generator("unknown")


class TestJupyterBookGenerator:
    def test_prepare_creates_toc(self, sample_project):
        """Test prepare creates _toc.yml."""
        from nblite.core.project import NbliteProject

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "_toc.yml").exists()

    def test_prepare_creates_config(self, sample_project):
        """Test prepare creates _config.yml."""
        from nblite.core.project import NbliteProject

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = JupyterBookGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "_config.yml").exists()


class TestMkDocsGenerator:
    def test_prepare_creates_config(self, sample_project):
        """Test prepare creates mkdocs.yml."""
        from nblite.core.project import NbliteProject

        project = NbliteProject.from_path(sample_project)
        output_dir = sample_project / "_docs"

        gen = MkDocsGenerator()
        gen.prepare(project, output_dir)

        assert (output_dir / "mkdocs.yml").exists()


class TestReadmeGeneration:
    def test_generate_readme(self, sample_project):
        """Test generating README from index notebook."""
        from nblite.docs.readme import generate_readme
        from nblite.core.project import NbliteProject

        # Create index notebook
        index_content = '''{"cells": [{"cell_type": "markdown", "source": "# My Package\\n\\nThis is my package.", "metadata": {}}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''
        (sample_project / "nbs" / "index.ipynb").write_text(index_content)

        project = NbliteProject.from_path(sample_project)
        readme_path = sample_project / "README.md"

        generate_readme(project, readme_path)

        assert readme_path.exists()
        content = readme_path.read_text()
        assert "My Package" in content
```

---

## Milestone 12: Function Notebook Export

### Tasks

- [ ] Implement `#|export_as_func` directive handling
- [ ] Implement `#|set_func_signature` parsing
- [ ] Implement `#|top_export` handling
- [ ] Implement `#|func_return` handling
- [ ] Implement `#|func_return_line` handling
- [ ] Generate proper function structure in module

### Pytest Tests

```python
# tests/test_function_export.py

import pytest
from pathlib import Path
from nblite.core.notebook import Notebook
from nblite.export.function_export import export_function_notebook


class TestFunctionNotebookExport:
    @pytest.fixture
    def function_notebook(self, tmp_path):
        """Create a function notebook."""
        nb_content = '''{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp my_workflow\\n#|export_as_func true", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|top_export\\nimport os\\nfrom typing import List", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef run_workflow(input_path: str, verbose: bool = False): ...", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|export\\ndata = load_data(input_path)\\nif verbose:\\n    print(f'Loaded {len(data)} items')", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|export\\nresult = process(data)", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|func_return\\nresult", "metadata": {}, "outputs": []}
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        nb_path = tmp_path / "workflow.ipynb"
        nb_path.write_text(nb_content)
        return Notebook.from_file(nb_path)

    def test_export_function_notebook(self, function_notebook, tmp_path):
        """Test exporting function notebook."""
        module_path = tmp_path / "my_workflow.py"

        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()

        # Check structure
        assert "import os" in content
        assert "from typing import List" in content
        assert "def run_workflow(input_path: str, verbose: bool = False):" in content
        assert "data = load_data(input_path)" in content
        assert "return result" in content

    def test_top_export_before_function(self, function_notebook, tmp_path):
        """Test top_export code appears before function."""
        module_path = tmp_path / "my_workflow.py"
        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()
        import_pos = content.find("import os")
        def_pos = content.find("def run_workflow")

        assert import_pos < def_pos

    def test_func_return_prepends_return(self, function_notebook, tmp_path):
        """Test func_return directive prepends return."""
        module_path = tmp_path / "my_workflow.py"
        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()
        assert "return result" in content

    def test_func_return_line_inline(self, tmp_path):
        """Test func_return_line works inline."""
        nb_content = '''{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp test\\n#|export_as_func true", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef compute(): ...", "metadata": {}, "outputs": []},
                {"cell_type": "code", "source": "#|export\\nx = calculate()\\nx #|func_return_line", "metadata": {}, "outputs": []}
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }'''
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "test.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        assert "return x" in content

    def test_non_exported_cells_excluded(self, function_notebook, tmp_path):
        """Test cells without export are excluded from function body."""
        module_path = tmp_path / "my_workflow.py"
        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()
        # The function signature cell content should not be in function body
        assert "..." not in content.split("def run_workflow")[1]
```

---

## Milestone 13: Advanced Features

### Tasks

- [ ] Implement `#|export_to` with ordering
  - [ ] Parse ORDER value
  - [ ] Sort cells by order during export
  - [ ] Handle negative order (before default_exp)
- [ ] Implement notebook templates
  - [ ] Template folder configuration
  - [ ] Jinja2 template rendering
  - [ ] `nbl new --template` support
- [ ] Implement `nbl from-module` command
  - [ ] Parse Python files
  - [ ] Create notebooks with cells
  - [ ] Add default_exp directives

### Pytest Tests

```python
# tests/test_advanced.py

import pytest
from nblite.export.export_to import collect_export_to_cells, sort_by_order


class TestExportToOrdering:
    def test_parse_order_value(self):
        """Test parsing order value from export_to."""
        from nblite.core.directive import parse_export_to_value

        result = parse_export_to_value("utils.helpers 50")
        assert result["module"] == "utils.helpers"
        assert result["order"] == 50

    def test_default_order(self):
        """Test default order is 100."""
        from nblite.core.directive import parse_export_to_value

        result = parse_export_to_value("utils.helpers")
        assert result["order"] == 100

    def test_negative_order(self):
        """Test negative order for before default_exp."""
        from nblite.core.directive import parse_export_to_value

        result = parse_export_to_value("utils.helpers -10")
        assert result["order"] == -10

    def test_sort_cells_by_order(self, tmp_path):
        """Test cells are sorted by order during export."""
        # Create notebooks with different orders
        nb1_content = '''{"cells": [{"cell_type": "code", "source": "#|default_exp utils\\n#|export\\ndef primary(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''

        nb2_content = '''{"cells": [{"cell_type": "code", "source": "#|export_to utils 50\\ndef before(): pass", "metadata": {}, "outputs": []}, {"cell_type": "code", "source": "#|export_to utils 150\\ndef after(): pass", "metadata": {}, "outputs": []}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}'''

        (tmp_path / "nb1.ipynb").write_text(nb1_content)
        (tmp_path / "nb2.ipynb").write_text(nb2_content)

        from nblite.core.notebook import Notebook
        nb1 = Notebook.from_file(tmp_path / "nb1.ipynb")
        nb2 = Notebook.from_file(tmp_path / "nb2.ipynb")

        cells = collect_export_to_cells([nb1, nb2], "utils")
        sorted_cells = sort_by_order(cells)

        # Order should be: before (50), primary (0 default), after (150)
        sources = [c.source_without_directives for c in sorted_cells]
        assert "before" in sources[0]
        assert "primary" in sources[1]
        assert "after" in sources[2]


class TestTemplates:
    def test_create_notebook_from_template(self, sample_project):
        """Test creating notebook from Jinja2 template."""
        from nblite.templates.renderer import render_template

        templates_dir = sample_project / "templates"
        templates_dir.mkdir()

        template_content = '''# %%
#|default_exp {{ module_name }}

# %%
#|export
def {{ function_name }}():
    """{{ description }}"""
    pass
'''
        (templates_dir / "api.pct.py.jinja").write_text(template_content)

        result = render_template(
            templates_dir / "api.pct.py.jinja",
            module_name="utils",
            function_name="process",
            description="Process data"
        )

        assert "#|default_exp utils" in result
        assert "def process():" in result


class TestFromModule:
    def test_convert_module_to_notebook(self, tmp_path):
        """Test converting Python module to notebook."""
        from nblite.cli.commands.from_module import module_to_notebook

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

        from nblite.core.notebook import Notebook
        nb = Notebook.from_file(nb_path)
        assert nb.default_exp == "utils"
```

---

## Running the Tests

```bash
# Run all tests
pytest

# Run tests for a specific milestone
pytest tests/test_directive.py
pytest tests/test_notebook.py

# Run with coverage
pytest --cov=nblite --cov-report=html

# Run tests matching a pattern
pytest -k "directive"
pytest -k "export"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## Progress Summary

| Milestone | Status | Tests Passing |
|-----------|--------|---------------|
| 1. Project Setup | [ ] | [ ] |
| 2. Directive System | [ ] | [ ] |
| 3. Cell & Notebook Classes | [ ] | [ ] |
| 4. Configuration System | [ ] | [ ] |
| 5. Code Location & PyFile | [ ] | [ ] |
| 6. Basic Export Pipeline | [ ] | [ ] |
| 7. NbliteProject Class | [ ] | [ ] |
| 8. CLI Foundation | [ ] | [ ] |
| 9. Git Integration | [ ] | [ ] |
| 10. Extension System | [ ] | [ ] |
| 11. Documentation Generation | [ ] | [ ] |
| 12. Function Notebook Export | [ ] | [ ] |
| 13. Advanced Features | [ ] | [ ] |

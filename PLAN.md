# nblite v2 - Development Plan

This document outlines the comprehensive development plan for nblite v2, a notebook-driven Python package development tool.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Data Model](#2-core-data-model)
3. [Directive System](#3-directive-system)
4. [Export System](#4-export-system)
5. [Project Management](#5-project-management)
6. [Extension/Hooks System](#6-extensionhooks-system)
7. [Git Integration](#7-git-integration)
8. [Documentation Generation](#8-documentation-generation)
9. [CLI Specification](#9-cli-specification)
10. [Lower Priority Features](#10-lower-priority-features)
11. [Migration from v1](#11-migration-from-v1)
12. [Implementation Order](#12-implementation-order)

---

## 1. Architecture Overview

### 1.1 Dependencies

- **notebookx**: Core dependency for notebook parsing and format conversion
  - Use `notebookx.Notebook` as the base class for `nblite.Notebook`
  - Use `notebookx.Format` for format handling (ipynb, percent)
  - Use `notebookx.CleanOptions` for notebook cleaning

- **pydantic**: Configuration validation and data models
- **typer**: CLI framework (with lazy imports for performance)
- **rich**: Terminal output formatting
- **jinja2**: Templates for notebook creation and docs
- **toml/tomli**: TOML configuration parsing

### 1.2 Module Structure

```
nblite/
├── __init__.py              # Public API exports
├── core/
│   ├── __init__.py
│   ├── notebook.py          # Notebook class (extends notebookx)
│   ├── cell.py              # Cell wrapper with directive support
│   ├── directive.py         # Directive parsing and representation
│   ├── pyfile.py            # PyFile class for .py module files
│   └── project.py           # NbliteProject class
├── config/
│   ├── __init__.py
│   ├── schema.py            # Pydantic models for nblite.toml
│   └── loader.py            # Config loading and validation
├── export/
│   ├── __init__.py
│   ├── pipeline.py          # Export pipeline orchestration
│   ├── percent_export.py    # Export to percent format
│   ├── module_export.py     # Export to Python module
│   └── modes.py             # Export mode handling
├── sync/
│   ├── __init__.py
│   ├── twins.py             # Twin file management
│   └── lineage.py           # Lineage tracking
├── git/
│   ├── __init__.py
│   ├── hooks.py             # Git hook management
│   └── staging.py           # Staging validation
├── docs/
│   ├── __init__.py
│   ├── generator.py         # Documentation generation
│   └── renderers/           # Pluggable doc renderers
├── extensions/
│   ├── __init__.py
│   ├── loader.py            # Extension loading
│   └── hooks.py             # Hook registry
├── cli/
│   ├── __init__.py
│   ├── app.py               # Main typer app
│   └── commands/            # CLI command modules
│       ├── export.py
│       ├── docs.py
│       ├── git.py
│       └── ...
├── templates/
│   └── assets/              # Template files
└── utils/
    └── __init__.py
```

---

## 2. Core Data Model

### 2.1 Notebook Class

Extends `notebookx.Notebook` with nblite-specific functionality.

```python
class Notebook(notebookx.Notebook):
    """
    Extended Notebook class with directive parsing and nblite metadata.

    Attributes:
        cells: List[Cell]  # Wrapped cells with directive support
        directives: dict[str, list[Directive]]  # All directives indexed by name
        source_path: Optional[Path]  # Original file path
        code_location: Optional[str]  # Code location key this notebook belongs to
    """

    @classmethod
    def from_file(cls, path: Path, format: Optional[Format] = None) -> "Notebook":
        """Load notebook from file with directive parsing."""

    @classmethod
    def from_notebookx(cls, nb: notebookx.Notebook, source_path: Optional[Path] = None) -> "Notebook":
        """Create from a notebookx Notebook instance."""

    @property
    def directives(self) -> dict[str, list[Directive]]:
        """All directives in the notebook, indexed by directive name."""

    def get_directive(self, name: str) -> Optional[Directive]:
        """Get the first (or only) directive with the given name."""

    def get_directives(self, name: str) -> list[Directive]:
        """Get all directives with the given name."""

    @property
    def default_exp(self) -> Optional[str]:
        """The default export module name from #|default_exp directive."""

    @property
    def exported_cells(self) -> list[Cell]:
        """Cells marked for export with #|export directive."""
```

### 2.2 Cell Class

Wrapper around notebookx cells with directive support.

```python
class Cell:
    """
    Wrapper around notebookx cell with directive parsing.

    Attributes:
        inner: notebookx.Cell  # The underlying notebookx cell
        directives: dict[str, list[Directive]]  # Directives in this cell
        index: int  # Cell index in the notebook
    """

    @property
    def source(self) -> str:
        """Cell source code."""

    @property
    def source_without_directives(self) -> str:
        """Source with directive lines removed."""

    @property
    def is_code(self) -> bool
    @property
    def is_markdown(self) -> bool
    @property
    def is_raw(self) -> bool

    def has_directive(self, name: str) -> bool:
        """Check if cell has a specific directive."""

    def get_directive(self, name: str) -> Optional[Directive]:
        """Get first directive with given name, or None."""
```

### 2.3 Directive Class

```python
@dataclass
class Directive:
    """
    Represents a single directive in a notebook cell.

    Attributes:
        cell: Cell  # Reference to the containing cell
        line_num: int  # Line number within the cell (0-indexed)
        py_code: str  # Code before the directive comment on this line
        name: str  # Directive name (e.g., "export", "default_exp")
        value: str  # Raw string value after the directive name
        value_parsed: Any  # Parsed value (if parser registered)
        value_is_dict: bool  # Whether value was parsed as dict
    """

    @classmethod
    def parse_from_line(cls, line: str, cell: Cell, line_num: int) -> Optional["Directive"]:
        """Parse a directive from a source line."""

    @classmethod
    def parse_cell(cls, cell: Cell) -> list["Directive"]:
        """Parse all directives from a cell."""
```

### 2.4 Directive Parsing Rules

```python
# Single line directive
#|directive_name value

# Directive with no value
#|directive_name

# Multi-word value (treated as single string)
#|directive_name this is all one string

# Multi-line directive (continuation with \)
#|directive_name \
#   key1=value1 \
#   key2=value2

# Escaped backslash
#|directive_name this has a \\

# Inline directive (after code)
def foo(): return value #|directive_name value

# Directive value types:
# - By default, value is a string
# - If a parser function is registered for the directive, value_parsed is populated
# - value_parsed == value if no parser is registered
```

### 2.5 PyFile Class

Represents a Python module file (.py).

```python
class PyFile:
    """
    Represents a Python module file in the project.

    Attributes:
        path: Path  # Absolute path to the file
        content: str  # File content
        is_autogenerated: bool  # Whether file has AUTOGENERATED header
        source_notebook: Optional[Path]  # Path to source notebook if autogenerated
        cells: list[PyFileCell]  # Parsed cell structure (for percent-style modules)
    """

    @classmethod
    def from_file(cls, path: Path) -> "PyFile":
        """Load a Python file."""

    @property
    def module_path(self) -> str:
        """Dotted module path relative to package root."""

    def get_source_cell_reference(self, cell_index: int) -> Optional[tuple[Path, int]]:
        """Get the source notebook and cell for a given module cell."""
```

### 2.6 NbliteProject Class

The central class representing an entire nblite project.

```python
class NbliteProject:
    """
    Represents an entire nblite project with all code locations and lineages.

    Attributes:
        root_path: Path  # Project root directory
        config: NbliteConfig  # Parsed configuration
        code_locations: dict[str, CodeLocation]  # All code locations
        notebooks: dict[Path, Notebook]  # All loaded notebooks
        py_files: dict[Path, PyFile]  # All loaded Python files
    """

    @classmethod
    def from_path(cls, path: Path = None) -> "NbliteProject":
        """
        Load project from path. If path is None, searches upward for nblite.toml.
        """

    @classmethod
    def find_project_root(cls, start_path: Path = None) -> Path:
        """Find project root by searching for nblite.toml."""

    def get_code_location(self, key: str) -> CodeLocation:
        """Get a code location by key."""

    def get_notebooks(self, code_location: str = None) -> list[Notebook]:
        """Get all notebooks, optionally filtered by code location."""

    def get_notebook_twins(self, notebook: Notebook) -> list[Path]:
        """Get all twin paths for a notebook."""

    def get_notebook_lineage(self, notebook: Notebook) -> NotebookLineage:
        """Get the full lineage (source → exports) for a notebook."""

    def export(self,
               pipeline: str = None,
               notebooks: list[Path] = None,
               hooks: ExtensionHooks = None) -> ExportResult:
        """Run the export pipeline."""

    def clean(self,
              notebooks: list[Path] = None,
              options: CleanOptions = None) -> None:
        """Clean notebooks."""

    def validate_staging(self) -> ValidationResult:
        """Validate git staging state."""
```

### 2.7 Code Location Classes

```python
@dataclass
class CodeLocation:
    """
    Represents a code location in the project.

    Attributes:
        key: str  # Location key (e.g., "nbs", "pts", "lib")
        path: Path  # Directory path relative to project root
        format: str  # Format: "ipynb", "percent", "module"
        export_mode: ExportMode  # How to export to this location
        files: list[Path]  # All files in this location
    """

    @property
    def file_ext(self) -> str:
        """File extension for this format."""

    @property
    def is_notebook(self) -> bool:
        """Whether this is a notebook format (not module)."""

    def get_files(self, ignore_dunders: bool = True, ignore_hidden: bool = True) -> list[Path]:
        """Get all files in this code location."""


class ExportMode(Enum):
    """Export mode for module code locations."""
    PERCENT = "percent"  # Export as percent-style Python with cell markers
    PY = "py"  # Export as plain Python without cell markers


@dataclass
class NotebookLineage:
    """
    Tracks the lineage of a notebook through the export pipeline.

    Attributes:
        source: Path  # Original source notebook path
        twins: dict[str, Path]  # Twin paths by code location key
        module_path: Optional[Path]  # Exported module path if applicable
        export_chain: list[tuple[str, str]]  # Export rules applied
    """
```

---

## 3. Directive System

### 3.1 Built-in Directives

**Export Directives:**
| Directive | Description | Value | In Topmatter |
|-----------|-------------|-------|--------------|
| `#\|default_exp` | Set default module export path | `module.path` | Yes |
| `#\|export` | Export cell to default module | none | Yes |
| `#\|exporti` | Export inline (internal) | none | Yes |
| `#\|export_to` | Export to specific module | `module.path [ORDER]` | Yes |

**Evaluation Directives:**
| Directive | Description | Value | In Topmatter |
|-----------|-------------|-------|--------------|
| `#\|eval: false` | Skip cell execution | `false` | Yes |
| `#\|skip_evals` | Skip this and following cells | none | Yes |
| `#\|skip_evals_stop` | Resume evaluation | none | Yes |

**Documentation Directives:**
| Directive | Description | Value | In Topmatter |
|-----------|-------------|-------|--------------|
| `#\|hide` | Hide cell from docs | none | Yes |
| `#\|hide_input` | Hide input, show output | none | Yes |
| `#\|hide_output` | Show input, hide output | none | Yes |

**Function Export Directives:**
| Directive | Description | Value | In Topmatter |
|-----------|-------------|-------|--------------|
| `#\|export_as_func` | Export notebook as function | `true` | Yes |
| `#\|set_func_signature` | Set function signature | `def name(args): ...` | Yes |
| `#\|top_export` | Code at module level (before function) | none | Yes |
| `#\|func_return` | Prepend `return` to first line of cell | none | Yes |
| `#\|func_return_line` | Prepend `return` to this line (inline) | none | No |

### 3.2 Directive Definitions

Instead of just "directive parsers", we have **directive definitions** that specify:
- How directive values are parsed
- Where directives can appear (topmatter requirement)
- Other validation rules

```python
@dataclass
class DirectiveDefinition:
    """
    Defines the rules for a directive.

    Attributes:
        name: Directive name (e.g., "export", "default_exp")
        in_topmatter: If True, directive must be placed in topmatter (top of cell, before code)
        value_parser: Optional function to parse the value string
        allows_inline: If True, directive can appear after code on same line
        description: Human-readable description
    """
    name: str
    in_topmatter: bool = True
    value_parser: Optional[Callable[[str], Any]] = None
    allows_inline: bool = False
    description: str = ""

# Global registry for directive definitions
_directive_definitions: dict[str, DirectiveDefinition] = {}

def register_directive(definition: DirectiveDefinition):
    """Register a directive definition."""
    _directive_definitions[definition.name] = definition

def get_directive_definition(name: str) -> Optional[DirectiveDefinition]:
    """Get the definition for a directive."""
    return _directive_definitions.get(name)
```

### 3.3 Topmatter Concept

**Topmatter** refers to directives that appear at the top of a cell, before any code (ignoring whitespace and empty lines).

```python
# %% Cell with topmatter directives

#|default_exp utils
#|export

def my_function():  # Code starts here
    pass
```

In this example, `#|default_exp` and `#|export` are in the topmatter.

**Invalid topmatter** (directive after code):
```python
# %%
#|export
def my_function():
    pass
#|hide  # ERROR: hide requires topmatter but appears after code
```

**Directives that require topmatter:**
- `export`, `exporti`, `export_to`, `default_exp`
- `top_export`, `set_func_signature`, `export_as_func`, `func_return`
- `hide`, `hide_input`, `hide_output`
- `eval`, `skip_evals`, `skip_evals_stop`

**Directives that allow inline (after code):**
- `func_return_line` - Must appear inline: `my_value #|func_return_line`

### 3.4 Built-in Directive Definitions

```python
# Export directives
register_directive(DirectiveDefinition(
    name="export",
    in_topmatter=True,
    description="Export cell to default module"
))
register_directive(DirectiveDefinition(
    name="default_exp",
    in_topmatter=True,
    value_parser=str.strip,
    description="Set default export module path"
))
register_directive(DirectiveDefinition(
    name="func_return_line",
    in_topmatter=False,
    allows_inline=True,
    description="Prepend 'return' to this line"
))

# Example built-in value parsers
def parse_bool_false(value: str) -> bool:
    return value.strip().lower() != "false"

def parse_bool_true(value: str) -> bool:
    return value.strip().lower() == "true"

register_directive(DirectiveDefinition(
    name="eval",
    in_topmatter=True,
    value_parser=parse_bool_false,
    description="Skip cell execution if false"
))
register_directive(DirectiveDefinition(
    name="export_as_func",
    in_topmatter=True,
    value_parser=parse_bool_true,
    description="Export notebook as callable function"
))
```

### 3.5 export_to Directive

The `#|export_to` directive allows cells to be exported to arbitrary modules:

```python
#|export_to utils.helpers  # Export to utils/helpers.py

#|export_to utils.helpers 10  # Export with explicit order (higher = later)
```

**Ordering rules:**
1. If a notebook has `#|default_exp` for a module, its cells export first (order 0)
2. Cells with `#|export_to` are ordered by their ORDER value (default: 100)
3. Negative ORDER values export before `#|default_exp` cells
4. Within same order, alphabetical by notebook name

---

## 4. Export System

### 4.1 Export Pipeline

The export pipeline is defined in `nblite.toml`:

```toml
export_pipeline = """
nbs -> pts
pts -> lib
"""

# Or explicit rules
[[export_rule]]
from = "nbs"
to = "pts"

[[export_rule]]
from = "pts"
to = "lib"
```

### 4.2 Export Modes

Configure how modules are exported in the code location definition:

```toml
[cl.lib]
path = "mypackage"
format = "module"
export_mode = "percent"  # default: include cell markers
# OR
export_mode = "py"  # plain Python, no cell markers

# Per-file override in nblite.toml
[[cl.lib.file_overrides]]
pattern = "cli.py"
export_mode = "py"

# Global options
[export]
include_autogenerated_warning = true  # Include "# AUTOGENERATED!" header
```

### 4.3 Export Mode: percent (default)

Exported Python files include cell markers showing source:

```python
# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/utils.ipynb

# %% ../nbs/api/utils.ipynb 0
__all__ = ['process_data', 'validate_input']

# %% ../nbs/api/utils.ipynb 3
def process_data(data):
    """Process the input data."""
    return data.strip()

# %% ../nbs/api/utils.ipynb 5
def validate_input(value):
    """Validate input value."""
    if not value:
        raise ValueError("Empty input")
    return True
```

### 4.4 Export Mode: py

Plain Python export without cell markers:

```python
# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/utils.ipynb

__all__ = ['process_data', 'validate_input']

def process_data(data):
    """Process the input data."""
    return data.strip()

def validate_input(value):
    """Validate input value."""
    if not value:
        raise ValueError("Empty input")
    return True
```

### 4.5 Module Export Process

```python
def export_notebook_to_module(
    notebook: Notebook,
    module_path: Path,
    export_mode: ExportMode,
    include_warning: bool = True,
    source_ref_style: str = "relative"  # or "absolute"
) -> None:
    """
    Export notebook cells to a Python module.

    Steps:
    1. Collect cells with #|export, #|exporti, #|export_to directives
    2. Extract __all__ from cell contents
    3. Remove directive lines from source
    4. Format according to export_mode
    5. Write to module_path
    """
```

### 4.6 Function Notebook Export

Function notebooks allow you to write a notebook that becomes a callable function when exported. This is useful for scripts/workflows that you want to run step-by-step in a notebook but also call programmatically.

**Directives:**
- `#|export_as_func true` - Mark notebook for function export
- `#|set_func_signature` - Define the function signature (cell contains signature like `def main(arg1): ...`)
- `#|top_export` - Code placed at module level BEFORE the function (imports, decorators, constants)
- `#|func_return` - Prepend `return` to the first line of this cell
- `#|func_return_line` - Inline directive to prepend `return` to this line

**Example Source Notebook:**
```python
# %% Cell 1
#|default_exp my_workflow
#|export_as_func true

# %% Cell 2
#|top_export
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Starting...")
        return func(*args, **kwargs)
    return wrapper

# %% Cell 3
#|set_func_signature
@my_decorator
def run_workflow(input_path: str, verbose: bool = False): ...

# %% Cell 4
#|export
data = load_data(input_path)
if verbose:
    print(f"Loaded {len(data)} items")

# %% Cell 5
#|export
result = process_data(data)

# %% Cell 6
#|func_return
result
```

**Exported Module (my_workflow.py):**
```python
# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/my_workflow.ipynb

# %% top_export
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Starting...")
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def run_workflow(input_path: str, verbose: bool = False):
    # AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/my_workflow.ipynb

    # %% auto 0
    __all__ = ['data', 'result']

    # %% ../nbs/my_workflow.ipynb 4
    data = load_data(input_path)
    if verbose:
        print(f"Loaded {len(data)} items")

    # %% ../nbs/my_workflow.ipynb 5
    result = process_data(data)

    return result
```

**Inline return with `#|func_return_line`:**
```python
# %% Cell
#|export
result = process_data(data)
result #|func_return_line  # This line becomes: return result
```

---

## 5. Project Management

### 5.1 Configuration Schema (nblite.toml)

```toml
# Export pipeline definition
export_pipeline = """
nbs -> pts
pts -> lib
"""

# Documentation settings
docs_cl = "nbs"  # Code location for documentation
docs_title = "My Package"
docs_generator = "jupyterbook"  # or "mkdocs", "sphinx"

# Template settings
[templates]
folder = "templates"  # Template folder path
default = "default.ipynb"  # Default template for nbl new

# Code locations
[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pts]
path = "pts"
format = "percent"

[cl.lib]
path = "mypackage"
format = "module"
export_mode = "percent"  # or "py"

# Extension settings - supports multiple extensions
# Can specify file paths or Python import paths
[[extensions]]
path = "nblite_ext.py"  # File path

[[extensions]]
path = "scripts/custom_hooks.py"  # Another file

[[extensions]]
module = "mypackage.nblite_extension"  # Python import path

# Export options
[export]
include_autogenerated_warning = true
cell_reference_style = "relative"  # or "absolute"

# Git integration
[git]
auto_clean = true  # Clean notebooks on commit
auto_export = true  # Run export on commit
validate_staging = true  # Validate staging on commit
```

### 5.2 Configuration Pydantic Models

```python
class ExportRule(BaseModel):
    from_key: str
    to_key: str

class CodeLocationConfig(BaseModel):
    path: str
    format: Literal["ipynb", "percent", "module"]
    export_mode: ExportMode = ExportMode.PERCENT

class TemplatesConfig(BaseModel):
    folder: str = "templates"
    default: Optional[str] = None

class ExtensionEntry(BaseModel):
    """Single extension entry - either file path or module import."""
    path: Optional[str] = None  # File path
    module: Optional[str] = None  # Python import path

    @model_validator(mode='after')
    def check_path_or_module(self):
        if not self.path and not self.module:
            raise ValueError("Either 'path' or 'module' must be specified")
        if self.path and self.module:
            raise ValueError("Cannot specify both 'path' and 'module'")
        return self

class ExportConfig(BaseModel):
    include_autogenerated_warning: bool = True
    cell_reference_style: Literal["relative", "absolute"] = "relative"

class GitConfig(BaseModel):
    auto_clean: bool = True
    auto_export: bool = True
    validate_staging: bool = True

class NbliteConfig(BaseModel):
    export_pipeline: list[ExportRule]
    code_locations: dict[str, CodeLocationConfig]
    docs_cl: Optional[str] = None
    docs_title: Optional[str] = None
    docs_generator: str = "jupyterbook"  # or "mkdocs"
    templates: TemplatesConfig = TemplatesConfig()
    extensions: list[ExtensionEntry] = []  # Multiple extensions supported
    export: ExportConfig = ExportConfig()
    git: GitConfig = GitConfig()
```

---

## 6. Extension/Hooks System

### 6.1 Hook Types

Extensions can register callbacks for various events:

```python
class HookType(Enum):
    # Export hooks
    PRE_EXPORT = "pre_export"  # Before export starts
    POST_EXPORT = "post_export"  # After export completes
    PRE_NOTEBOOK_EXPORT = "pre_notebook_export"  # Before each notebook
    POST_NOTEBOOK_EXPORT = "post_notebook_export"  # After each notebook

    # Cell processing hooks
    PRE_CELL_EXPORT = "pre_cell_export"  # Before cell is exported
    POST_CELL_EXPORT = "post_cell_export"  # After cell is exported

    # Clean hooks
    PRE_CLEAN = "pre_clean"
    POST_CLEAN = "post_clean"

    # Documentation hooks
    PRE_DOCS_BUILD = "pre_docs_build"
    POST_DOCS_BUILD = "post_docs_build"

    # Git hooks
    PRE_COMMIT = "pre_commit"
    PRE_STAGING_VALIDATE = "pre_staging_validate"

    # Directive hooks
    DIRECTIVE_PARSED = "directive_parsed"  # Custom directive processing
```

### 6.2 Hook Registry

```python
class HookRegistry:
    """Registry for extension hooks."""

    _hooks: dict[HookType, list[Callable]] = {}

    @classmethod
    def register(cls, hook_type: HookType, callback: Callable):
        """Register a callback for a hook type."""
        if hook_type not in cls._hooks:
            cls._hooks[hook_type] = []
        cls._hooks[hook_type].append(callback)

    @classmethod
    def trigger(cls, hook_type: HookType, **context) -> list[Any]:
        """Trigger all callbacks for a hook type."""
        results = []
        for callback in cls._hooks.get(hook_type, []):
            result = callback(**context)
            results.append(result)
        return results

    @classmethod
    def clear(cls):
        """Clear all registered hooks."""
        cls._hooks.clear()

# Convenience decorator
def hook(hook_type: HookType):
    """Decorator to register a function as a hook."""
    def decorator(func):
        HookRegistry.register(hook_type, func)
        return func
    return decorator
```

### 6.3 Extension Loading

Extensions are Python files or modules that are loaded at startup:

```python
# nblite_ext.py (extension file)

from nblite.extensions import hook, HookType, HookRegistry
from nblite.core import Directive

# Register custom directive parser
from nblite.core.directive import register_directive_parser

def parse_my_directive(value: str) -> dict:
    """Custom parser for #|my_directive."""
    return {"parsed": value.strip()}

register_directive_parser("my_directive", parse_my_directive)

# Register hook callbacks
@hook(HookType.PRE_EXPORT)
def before_export(project, **kwargs):
    """Called before export starts."""
    print(f"Starting export for {project.root_path}")

@hook(HookType.POST_CELL_EXPORT)
def after_cell(cell, module_path, **kwargs):
    """Called after each cell is exported."""
    if cell.has_directive("my_directive"):
        directive = cell.get_directive("my_directive")
        # Do something with custom directive
        pass

# Can also register programmatically
HookRegistry.register(HookType.POST_EXPORT, lambda **ctx: print("Export done!"))
```

### 6.4 CLI Extension Loading

```bash
# Load extension from file path
nbl export --extension nblite_ext.py

# Load extension from Python module import path
nbl export --extension mypackage.nblite_extension

# Load multiple extensions (can mix file paths and module paths)
nbl export --extension nblite_ext.py --extension mypackage.hooks

# Default: load from nblite.toml [[extensions]] section
nbl export
```

**Extension Loading Logic:**
1. If `--extension` flags are provided, load those extensions
2. Otherwise, load extensions from `[[extensions]]` in nblite.toml
3. Extensions are loaded in order specified
4. Each extension can register hooks and directive definitions

---

## 7. Git Integration

### 7.1 Improved Hook Installation

Support for nblite projects in subdirectories:

```python
def install_hooks(project: NbliteProject, force: bool = False) -> None:
    """
    Install git hooks for an nblite project.

    Features:
    - Works with projects in repo subdirectories
    - Adds to existing hooks instead of overwriting
    - Uses markers for clean uninstall
    - Supports multiple nblite projects per repo
    """
```

### 7.2 Hook File Format

```bash
#!/bin/sh

# ... existing hook content ...

# BEGIN NBLITE HOOK: /path/to/project
if [ "$NBL_DISABLE_HOOKS" != "true" ]; then
    cd "/path/to/project" && nbl hook pre-commit
fi
# END NBLITE HOOK: /path/to/project

# ... more nblite hooks for other projects ...
```

### 7.3 Hook Commands

```bash
# Install hooks (adds to existing hooks)
nbl install-hooks

# Uninstall hooks (removes nblite section from hook file)
nbl uninstall-hooks

# Run hook manually (called by git hook)
nbl hook pre-commit
nbl hook post-commit
```

### 7.4 Staging Validation

Enhanced staging validation:

```python
def validate_staging(project: NbliteProject) -> ValidationResult:
    """
    Validate git staging state.

    Checks:
    1. All staged notebooks are clean (no outputs/metadata)
    2. All twins of staged files are also staged
    3. No partial staging of related files

    Returns:
        ValidationResult with errors and warnings
    """

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    unclean_notebooks: list[Path]
    unstaged_twins: list[tuple[Path, list[Path]]]  # (staged, unstaged twins)
```

---

## 8. Documentation Generation

### 8.1 Modular Documentation System

nblite v2 supports **multiple documentation generators** through a pluggable architecture. Users can choose which generator to use, and new generators can be added.

**Built-in Generators:**

1. **Jupyter Book** (`jupyterbook`)
   - Native Jupyter notebook support
   - pip-installable (`pip install jupyter-book`)
   - MyST Markdown for enhanced features
   - Can execute notebooks during build
   - HTML and PDF output

2. **MkDocs** (`mkdocs`)
   - Modern Material theme
   - Fast builds
   - pip-installable (`pip install mkdocs mkdocs-material mkdocs-jupyter`)
   - Great for simpler documentation needs

3. **Future: Quarto** (`quarto`)
   - Can be added later for users who prefer Quarto
   - Would require external Quarto installation

### 8.2 Documentation Configuration

```toml
# nblite.toml
docs_cl = "nbs"
docs_title = "My Package"
docs_generator = "jupyterbook"  # or "mkdocs"

[docs]
output_folder = "_docs"
execute_notebooks = false
exclude_patterns = ["__*", ".*"]

[docs.jupyterbook]
# Jupyter Book specific options
toc_depth = 2
execute_notebooks = "auto"

[docs.mkdocs]
# MkDocs specific options
theme = "material"
```

### 8.3 Documentation Generator Interface

```python
class DocsGenerator(Protocol):
    """Protocol for documentation generators."""

    def prepare(self, project: NbliteProject, output_dir: Path) -> None:
        """Prepare documentation source files."""

    def build(self, output_dir: Path, final_dir: Path) -> None:
        """Build documentation to final output."""

    def preview(self, output_dir: Path) -> None:
        """Start preview server."""

class JupyterBookGenerator(DocsGenerator):
    """Jupyter Book documentation generator."""

class MkDocsGenerator(DocsGenerator):
    """MkDocs documentation generator."""
```

### 8.4 Documentation Commands

```bash
# Build documentation
nbl docs build [-o OUTPUT_DIR]

# Preview documentation (live reload)
nbl docs preview

# Generate README from index notebook
nbl docs readme
```

---

## 9. CLI Specification

### 9.1 Command Overview

```
nbl - nblite CLI

USAGE:
    nbl [OPTIONS] <COMMAND>

OPTIONS:
    --version           Show version
    --extension FILE    Load extension file
    -r, --root PATH     Project root path
    --help              Show help

COMMANDS:
    # Project Management
    init                Initialize new nblite project
    new                 Create new notebook from template

    # Export & Sync
    export              Run export pipeline
    clean               Clean notebooks (wraps nbx clean with nblite.toml options)
    clear               Clear code location(s)

    # Execution
    fill                Execute notebooks and fill outputs
    test                Test notebooks without modifying (dry-run)
    run                 Run specific notebooks

    # Conversion
    convert             Convert notebook between formats (wraps nbx convert)

    # Documentation
    docs build          Build documentation
    docs preview        Preview documentation
    docs readme         Generate README from index notebook

    # Git Integration
    git add             Stage files with export and cleaning
    git validate        Validate staging state
    install-hooks       Install git hooks
    uninstall-hooks     Remove git hooks
    hook                Run hook (internal use)

    # Utilities
    info                Show project information
    list                List notebooks/files in code locations
```

### 9.2 Detailed Command Specifications

#### `nbl init`
```
Initialize a new nblite project.

USAGE:
    nbl init [OPTIONS]

OPTIONS:
    -n, --name NAME     Module name (default: directory name)
    -p, --path PATH     Project path (default: current directory)
    --use-defaults      Use defaults without prompting
    --template NAME     Project template to use
```

#### `nbl new`
```
Create a new notebook.

USAGE:
    nbl new <PATH> [OPTIONS]

ARGUMENTS:
    PATH                Notebook path (e.g., nbs/api/utils.ipynb)

OPTIONS:
    -n, --name NAME     Module name for default_exp
    -t, --title TITLE   Notebook title
    --template NAME     Template to use
    --no-export         Don't include default_exp directive
```

#### `nbl export`
```
Run the export pipeline.

USAGE:
    nbl export [OPTIONS] [NOTEBOOKS...]

ARGUMENTS:
    NOTEBOOKS           Specific notebooks to export (optional)

OPTIONS:
    --pipeline RULES    Override export pipeline
    --extension FILE    Load extension file
    --dry-run           Show what would be exported
```

#### `nbl clean`
```
Clean notebooks by removing outputs and metadata.
Wraps `nbx clean` with options from nblite.toml.

USAGE:
    nbl clean [OPTIONS] [NOTEBOOKS...]

ARGUMENTS:
    NOTEBOOKS           Notebooks to clean (default: all ipynb in project)

OPTIONS:
    --remove-outputs    Remove cell outputs
    --remove-metadata   Remove cell metadata (default: true)
    --exclude-dunders   Exclude __* notebooks
    --exclude-hidden    Exclude .* notebooks

Note: Clean options can also be configured in nblite.toml [clean] section.
CLI options override config file options.
```

#### `nbl convert`
```
Convert notebook between formats.
This is a thin wrapper around `nbx convert` from notebookx.

USAGE:
    nbl convert <INPUT> <OUTPUT> [OPTIONS]

ARGUMENTS:
    INPUT               Input notebook path
    OUTPUT              Output notebook path

OPTIONS:
    --from FORMAT       Input format (auto-detected from extension if omitted)
    --to FORMAT         Output format (auto-detected from extension if omitted)

Note: This command delegates directly to notebookx for format conversion.
```

#### `nbl fill`
```
Execute notebooks and fill with outputs.

USAGE:
    nbl fill [OPTIONS] [NOTEBOOKS...]

ARGUMENTS:
    NOTEBOOKS           Notebooks to fill (default: all ipynb in project)

OPTIONS:
    -t, --timeout SECS  Cell execution timeout
    -n, --workers N     Number of parallel workers (default: 4)
    --remove-outputs    Remove existing outputs before fill
    --fill-unchanged    Fill even if notebook hasn't changed
    --silent            Suppress output
```

#### `nbl docs build`
```
Build project documentation.

USAGE:
    nbl docs build [OPTIONS]

OPTIONS:
    -o, --output PATH   Output directory (default: _docs)
    --generator NAME    Override docs generator
    --execute           Execute notebooks during build
```

#### `nbl install-hooks`
```
Install git hooks for the project.

USAGE:
    nbl install-hooks [OPTIONS]

OPTIONS:
    --force             Overwrite existing nblite hooks
```

#### `nbl info`
```
Show project information.

USAGE:
    nbl info [OPTIONS]

OPTIONS:
    --json              Output as JSON
```

### 9.3 CLI Implementation Notes

**Lazy Loading for Performance:**

```python
# cli/commands/export.py
import typer

app = typer.Typer()

@app.command()
def export(
    notebooks: list[str] = typer.Argument(None),
    pipeline: str = typer.Option(None),
):
    """Run the export pipeline."""
    # Import heavy modules inside function
    from nblite.core.project import NbliteProject
    from nblite.export.pipeline import run_pipeline

    project = NbliteProject.from_path()
    run_pipeline(project, notebooks=notebooks, pipeline=pipeline)
```

---

## 10. Lower Priority Features

### 10.1 Notebook Templates

```toml
# nblite.toml
[templates]
folder = "templates"
default = "standard.pct.py"
```

Template folder structure:
```
templates/
├── standard.pct.py      # Default template
├── api.ipynb            # API module template
├── test.ipynb           # Test notebook template
└── tutorial.md.jinja    # Tutorial template with Jinja
```

Usage:
```bash
nbl new nbs/utils.ipynb                    # Use default template
nbl new nbs/utils.ipynb --template api     # Use api template
```

### 10.2 Module Import Feature

Convert existing Python package to nblite notebooks:

```bash
nbl from-module mypackage [-o nbs/]
```

Process:
1. Read all .py files in package
2. Create one notebook per file
3. Single code cell with all content
4. Add `#|default_exp` based on module path
5. Optionally split into cells at function/class boundaries

### 10.3 export_to with Ordering

```python
# notebook_a.ipynb - has default_exp for utils
#|default_exp utils
#|export
def primary_func():
    pass

# notebook_b.ipynb - exports helper to same module
#|export_to utils 50  # Order 50 (before default 100)
def helper_before():
    pass

#|export_to utils 150  # Order 150 (after default 100)
def helper_after():
    pass

#|export_to utils -10  # Negative: before default_exp
CONSTANT = "value"
```

Resulting utils.py:
```python
# From notebook_b (order -10)
CONSTANT = "value"

# From notebook_a (default_exp, order 0)
def primary_func():
    pass

# From notebook_b (order 50)
def helper_before():
    pass

# From notebook_b (order 150)
def helper_after():
    pass
```

---

## 11. Migration from v1

### 11.1 Configuration Migration

v1 config:
```toml
export_pipeline = "nbs -> pts\npts -> lib"

[cl.lib]
path = "nblite"
```

v2 config (backward compatible):
```toml
export_pipeline = """
nbs -> pts
pts -> lib
"""

[cl.lib]
path = "nblite"
format = "module"
export_mode = "percent"  # New option with sensible default
```

### 11.2 Breaking Changes

1. **notebookx replaces jupytext/nbformat**: Internal conversion uses notebookx
2. **nbdev replacement**: Custom export logic replaces nbdev dependency
3. **Quarto replaced**: Jupyter Book or MkDocs for documentation
4. **New directive syntax**: Multi-line directives use `\` continuation

### 11.3 Migration Command

```bash
nbl migrate [--dry-run]
```

Handles:
- Config format updates
- Directive syntax updates (if any)
- Checks for deprecated features

---

## 12. Implementation Order

### Phase 1: Core Foundation
1. [ ] Set up project structure and dependencies
2. [ ] Implement `Directive` class with parsing
3. [ ] Implement `Cell` wrapper class
4. [ ] Implement `Notebook` class extending notebookx
5. [ ] Implement configuration loading (pydantic models)

### Phase 2: Export System
6. [ ] Implement `CodeLocation` class
7. [ ] Implement `PyFile` class
8. [ ] Implement basic export pipeline (notebook → notebook)
9. [ ] Implement module export with `percent` mode
10. [ ] Implement module export with `py` mode

### Phase 3: Project Management
11. [ ] Implement `NbliteProject` class
12. [ ] Implement twin tracking
13. [ ] Implement lineage tracking
14. [ ] Implement cleaning with notebookx

### Phase 4: CLI (Core Commands)
15. [ ] Set up typer app with lazy loading
16. [ ] Implement `nbl init`
17. [ ] Implement `nbl new`
18. [ ] Implement `nbl export`
19. [ ] Implement `nbl clean`
20. [ ] Implement `nbl fill`/`nbl test`

### Phase 5: Git Integration
21. [ ] Implement `nbl validate-staging`
22. [ ] Implement `nbl install-hooks` (with multi-project support)
23. [ ] Implement `nbl uninstall-hooks`
24. [ ] Implement `nbl git add`

### Phase 6: Extension System
25. [ ] Implement hook registry
26. [ ] Implement extension loading
27. [ ] Add CLI extension support

### Phase 7: Documentation
28. [ ] Implement Jupyter Book generator
29. [ ] Implement `nbl docs build`
30. [ ] Implement `nbl docs preview`
31. [ ] Implement README generation

### Phase 8: Advanced Features
32. [ ] Implement `export_to` directive with ordering
33. [ ] Implement templates system
34. [ ] Implement `nbl from-module`

### Phase 9: Testing & Polish
35. [ ] Comprehensive test suite
36. [ ] Documentation
37. [ ] Migration tooling
38. [ ] Performance optimization

---

## Design Decisions (Resolved)

1. **Documentation Generator**: Modular system supporting both Jupyter Book and MkDocs. Users choose via `docs_generator` in config. Extensible for future generators (including Quarto).

2. **nbdev Compatibility**: Clean break. All export logic implemented using notebookx. No nbdev dependency.

3. **Directive Syntax**: Maintain nbdev-style (`#|export`) with extensions for multi-line support using `\` continuation.

4. **Default Export Mode**: `percent` mode (with cell markers) is the default.

5. **Extensions**: Support multiple extensions. Each can be a file path OR Python import path. Configured in `[[extensions]]` array in nblite.toml or via `--extension` CLI flag.

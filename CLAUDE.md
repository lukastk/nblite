# CLAUDE.md - nblite v2 Contributor Guide

This document provides guidance for contributors (human and AI) working on the nblite v2 project.

---

## Project Overview

**nblite** is a notebook-driven Python package development tool, serving as a modern alternative to nbdev. It enables developers to write Python packages entirely in Jupyter notebooks, with automatic export to Python modules, synchronization between formats, and integrated documentation generation.

### What nblite Does

1. **Notebook → Module Export**: Convert Jupyter notebooks to Python packages using directives like `#|export`
2. **Format Synchronization**: Keep notebooks (ipynb), plaintext scripts (pct.py), and modules (.py) in sync
3. **Git Integration**: Pre-commit hooks for cleaning notebooks and validating staging
4. **Documentation**: Generate documentation sites from notebooks

### Core Dependency: notebookx

nblite v2 uses [notebookx](https://github.com/lukastk/notebookx) for all notebook parsing and format conversion. notebookx is a high-performance Rust library with Python bindings.

---

## Project Goals

### Primary Goals

1. **Simplicity**: Clean, intuitive API for notebook-driven development
2. **Performance**: Fast exports and conversions using notebookx
3. **Extensibility**: Hook system for custom workflows
4. **Git-Friendly**: Excellent git integration with clean diffs

### Non-Goals

1. **nbdev Compatibility**: Not aiming for drop-in replacement
2. **Notebook Execution**: We don't execute notebooks (except for `fill` command using nbconvert)
3. **IDE Integration**: Focus on CLI and library, not editor plugins

---

## Architecture Principles

### 1. notebookx as Foundation

All notebook parsing and format conversion goes through notebookx:

```python
import notebookx

# Parse notebook
nb = notebookx.Notebook.from_file("notebook.ipynb")

# Convert format
nb.to_file("notebook.pct.py", format=notebookx.Format.Percent)

# Clean
clean_nb = nb.clean(notebookx.CleanOptions.for_vcs())
```

nblite extends notebookx with directive parsing and project management.

### 2. Directive-Driven Behavior

All special behavior is controlled by directives in cell source:

```python
#|default_exp utils    # Set export module
#|export               # Mark cell for export
#|hide                 # Hide from documentation
```

Directives are comments, so notebooks remain valid Python/Jupyter files.

### 3. Code Locations

A project has multiple "code locations" - directories containing code in different formats:

```
project/
├── nbs/           # Source notebooks (ipynb)
├── pts/           # Plaintext scripts (pct.py)
└── mypackage/     # Python package (py)
```

The export pipeline defines how code flows between locations:
```
nbs → pts → mypackage
```

### 4. Lazy Loading for CLI Performance

Python CLIs can be slow due to import overhead. Always import heavy modules inside CLI functions:

```python
# GOOD - lazy import
@app.command()
def export():
    from nblite.core.project import NbliteProject  # Import inside function
    project = NbliteProject.from_path()
    project.export()

# BAD - top-level import slows CLI startup
from nblite.core.project import NbliteProject  # Don't do this in CLI modules

@app.command()
def export():
    project = NbliteProject.from_path()
```

### 5. Immutability Where Possible

Following notebookx's design, prefer returning new objects over mutation:

```python
# GOOD - returns new notebook
clean_nb = notebook.clean(options)

# AVOID - mutating in place
notebook.clean_in_place(options)
```

---

## Coding Conventions

### Python Style

- Python 3.10+ required (use modern type hints, `|` union syntax)
- Use `ruff` for formatting and linting
- Use `pydantic` for data validation and configuration
- Use `typer` for CLI
- Use `rich` for terminal output

### Type Hints

Always use type hints for function signatures:

```python
def export_notebook(
    notebook: Notebook,
    output_path: Path,
    mode: ExportMode = ExportMode.PERCENT,
) -> None:
    """Export notebook to Python module."""
    ...
```

### Naming Conventions

- Classes: `PascalCase` (e.g., `NbliteProject`, `CodeLocation`)
- Functions/methods: `snake_case` (e.g., `export_notebook`, `get_directives`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `DEFAULT_EXPORT_MODE`)
- Private: prefix with `_` (e.g., `_parse_directive_value`)

### Module Organization

```
nblite/
├── __init__.py          # Public API exports
├── core/                # Core data models
│   ├── notebook.py      # Notebook class
│   ├── cell.py          # Cell wrapper
│   ├── directive.py     # Directive parsing
│   └── project.py       # NbliteProject
├── config/              # Configuration
├── export/              # Export logic
├── git/                 # Git integration
├── docs/                # Documentation generation
├── extensions/          # Extension system
├── cli/                 # CLI commands
│   ├── app.py           # Main app
│   └── commands/        # Command modules
└── utils/               # Utilities
```

---

## Key Classes

### Notebook

Extends notebookx.Notebook with directive support:

```python
class Notebook(notebookx.Notebook):
    """Extended notebook with directive parsing."""

    @property
    def directives(self) -> dict[str, list[Directive]]:
        """All directives indexed by name."""

    @property
    def default_exp(self) -> str | None:
        """Module path from #|default_exp."""

    @property
    def exported_cells(self) -> list[Cell]:
        """Cells marked with #|export."""
```

### Directive

Represents a parsed directive:

```python
@dataclass
class Directive:
    cell: Cell              # Containing cell
    line_num: int           # Line in cell (0-indexed)
    py_code: str            # Code before directive on same line
    name: str               # Directive name
    value: str              # Raw value string
    value_parsed: Any       # Parsed value (if parser registered)
```

### NbliteProject

Central class for project management:

```python
class NbliteProject:
    """Represents an nblite project."""

    root_path: Path
    config: NbliteConfig
    code_locations: dict[str, CodeLocation]

    @classmethod
    def from_path(cls, path: Path = None) -> NbliteProject:
        """Load project, searching for nblite.toml if path not given."""

    def export(self, notebooks: list[Path] = None) -> ExportResult:
        """Run export pipeline."""

    def clean(self, notebooks: list[Path] = None) -> None:
        """Clean notebooks."""
```

---

## Directive System

### Parsing Rules

```python
# Basic directive
#|directive_name value

# No value
#|directive_name

# Multi-line (continuation)
#|directive_name \
#   continuation \
#   more

# Inline with code
x = 1 #|directive_name value

# Escaped backslash
#|directive_name path\\to\\file
```

### Topmatter

**Topmatter** refers to directives placed at the top of a cell, before any code. Most directives require topmatter placement:

```python
# GOOD - topmatter (directive before code)
#|export
def my_function():
    pass

# BAD - directive after code (invalid for most directives)
x = 1
#|export  # This won't work for directives requiring topmatter
def my_function():
    pass
```

### Built-in Directives

| Directive | Purpose | In Topmatter |
|-----------|---------|--------------|
| `#\|default_exp` | Set default export module | Yes |
| `#\|export` | Export cell to default module | Yes |
| `#\|exporti` | Export as internal (not in `__all__`) | Yes |
| `#\|export_to` | Export to specific module | Yes |
| `#\|export_as_func` | Export notebook as callable function | Yes |
| `#\|top_export` | Code placed before function definition | Yes |
| `#\|func_return` | Prepend `return` to first line of cell | Yes |
| `#\|func_return_line` | Prepend `return` to specific line | No (inline) |
| `#\|hide` | Hide from documentation | Yes |
| `#\|eval: false` | Skip cell execution | Yes |

### Directive Definitions

Directives are defined with rules specifying their behavior:

```python
from nblite.core.directive import DirectiveDefinition

@dataclass
class DirectiveDefinition:
    name: str
    in_topmatter: bool = True  # Must be placed in topmatter (top of cell, before code)
    value_parser: Callable[[str], Any] | None = None
    allows_inline: bool = False
    description: str = ""
```

Most directives must be in topmatter. The exception is `func_return_line` which is used inline:

```python
#|export
def compute():
    x = expensive_calculation()
    x  #|func_return_line
```

### Custom Directive Definitions

Register custom directives with their rules:

```python
from nblite.core.directive import register_directive

register_directive(DirectiveDefinition(
    name="my_directive",
    in_topmatter=True,
    value_parser=lambda v: {"key": v.strip()},
    description="My custom directive"
))

---

## Export System

### Export Pipeline

Defined in `nblite.toml`:

```toml
export_pipeline = """
nbs -> pts
pts -> lib
"""
```

### Export Modes

**percent** (default): Include cell markers in exported .py files:
```python
# %% ../nbs/utils.ipynb 3
def helper():
    pass
```

**py**: Plain Python without markers:
```python
def helper():
    pass
```

Configure per code location:
```toml
[cl.lib]
path = "mypackage"
format = "module"
export_mode = "percent"  # or "py"
```

---

## Extension System

### Hook Types

- `PRE_EXPORT` / `POST_EXPORT`: Before/after export pipeline
- `PRE_NOTEBOOK_EXPORT` / `POST_NOTEBOOK_EXPORT`: Per notebook
- `PRE_CELL_EXPORT` / `POST_CELL_EXPORT`: Per cell
- `DIRECTIVE_PARSED`: Custom directive handling

### Writing Extensions

```python
# nblite_ext.py
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def before_export(project, **kwargs):
    print(f"Exporting {project.root_path}")

@hook(HookType.POST_CELL_EXPORT)
def after_cell(cell, **kwargs):
    if cell.has_directive("my_directive"):
        # Custom processing
        pass
```

### Loading Extensions

Via CLI:
```bash
nbl export --extension nblite_ext.py
nbl export --extension mypackage.nblite_extension
```

Or in config (supports multiple extensions via file path OR Python import path):
```toml
# Multiple extensions
[[extensions]]
path = "nblite_ext.py"

[[extensions]]
module = "mypackage.nblite_extension"

[[extensions]]
path = "another_ext.py"
```

---

## Testing

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_notebook.py     # Notebook class tests
├── test_directive.py    # Directive parsing tests
├── test_export.py       # Export tests
├── test_project.py      # Project tests
└── fixtures/            # Test notebooks and configs
```

### Test Patterns

```python
import pytest
from nblite.core import Notebook, Directive

def test_directive_parsing():
    """Test basic directive parsing."""
    nb = Notebook.from_file("fixtures/test.ipynb")
    assert nb.default_exp == "test_module"
    assert len(nb.exported_cells) == 3

def test_export_percent_mode(tmp_path):
    """Test export with percent mode."""
    # Create test notebook
    # Run export
    # Verify output format

@pytest.fixture
def sample_project(tmp_path):
    """Create a sample nblite project."""
    # Set up project structure
    yield tmp_path
    # Cleanup
```

### Running Tests

```bash
pytest                    # All tests
pytest -x                 # Stop on first failure
pytest -k "directive"     # Tests matching pattern
pytest --cov=nblite       # With coverage
```

---

## CLI Development

### Adding Commands

1. Create command module in `cli/commands/`:

```python
# cli/commands/mycommand.py
import typer

app = typer.Typer()

@app.command()
def mycommand(
    path: str = typer.Argument(None, help="Path to process"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
):
    """My command description."""
    # Lazy imports
    from nblite.core.project import NbliteProject

    project = NbliteProject.from_path()
    # ... command logic
```

2. Register in main app:

```python
# cli/app.py
from .commands import mycommand

app.add_typer(mycommand.app, name="mycommand")
```

### CLI Guidelines

- Always use lazy imports inside command functions
- Use `typer.Argument` for required positional args
- Use `typer.Option` for optional flags
- Include help text for all parameters
- Use `rich` for formatted output

---

## Configuration

### nblite.toml Schema

```toml
# Export pipeline
export_pipeline = """
nbs -> pts
pts -> lib
"""

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
export_mode = "percent"

# Documentation
docs_cl = "nbs"
docs_title = "My Package"
docs_generator = "jupyterbook"  # or "mkdocs"

# Extensions (supports multiple)
[[extensions]]
path = "nblite_ext.py"

[[extensions]]
module = "mypackage.extension"

# Export options
[export]
include_autogenerated_warning = true

# Git integration
[git]
auto_clean = true
auto_export = true
```

### Pydantic Models

All config uses pydantic for validation:

```python
from pydantic import BaseModel

class CodeLocationConfig(BaseModel):
    path: str
    format: Literal["ipynb", "percent", "module"]
    export_mode: ExportMode = ExportMode.PERCENT

class NbliteConfig(BaseModel):
    export_pipeline: list[ExportRule]
    code_locations: dict[str, CodeLocationConfig]
    # ...
```

---

## Git Integration

### Hook Installation

Hooks support:
- Projects in repo subdirectories
- Multiple nblite projects per repo
- Non-destructive installation (adds to existing hooks)
- Clean uninstall with markers

### Hook File Format

```bash
#!/bin/sh

# BEGIN NBLITE HOOK: /path/to/project
if [ "$NBL_DISABLE_HOOKS" != "true" ]; then
    cd "/path/to/project" && nbl hook pre-commit
fi
# END NBLITE HOOK: /path/to/project
```

---

## Error Handling

### Error Types

```python
class NbliteError(Exception):
    """Base exception for nblite errors."""

class ConfigError(NbliteError):
    """Configuration error."""

class ExportError(NbliteError):
    """Export error."""

class DirectiveError(NbliteError):
    """Directive parsing error."""
```

### User-Friendly Errors

```python
# Good - helpful context
raise ConfigError(
    f"Code location '{key}' not found in nblite.toml. "
    f"Available locations: {', '.join(config.code_locations.keys())}"
)

# Bad - cryptic message
raise KeyError(key)
```

---

## Commit Guidelines

### IMPORTANT: Commit Early and Often

**This is critical for AI contributors:** Commit changes frequently as you make them. Do not accumulate large uncommitted changes.

**When to commit:**
- After implementing a new feature or part of a feature
- After fixing a bug
- After adding tests for new functionality
- After refactoring, even if small
- After making any meaningful change that works

**Why this matters:**
- Progress is saved and can be reviewed incrementally
- Easier to bisect and find issues
- Clearer history of what changed and why
- Reduced risk of losing work
- Makes code review easier

**Example workflow:**
```bash
# Working on directive parsing
# ... implement basic parsing ...
git add . && git commit -m "feat: implement basic directive parsing"

# ... add topmatter validation ...
git add . && git commit -m "feat: add topmatter validation for directives"

# ... add tests ...
git add . && git commit -m "test: add directive parsing tests"

# ... fix bug found during testing ...
git add . && git commit -m "fix: handle empty directive values"
```

### Commit Message Format

```
<type>: <short description>

<optional body>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
```
feat: add export_to directive support
fix: handle empty notebooks in export
refactor: extract directive parsing to separate module
```

---

## Dependencies

### Core Dependencies

- `notebookx`: Notebook parsing and conversion
- `pydantic`: Configuration validation
- `typer`: CLI framework
- `rich`: Terminal formatting
- `jinja2`: Templates
- `tomli`: TOML parsing (Python < 3.11)

### Development Dependencies

- `pytest`: Testing
- `pytest-cov`: Coverage
- `ruff`: Linting and formatting
- `mypy`: Type checking

### Avoiding Bloat

Before adding a dependency:
1. Is it well-maintained?
2. Can we implement the feature in < 100 lines?
3. Does it add significant transitive dependencies?

---

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def export_notebook(
    notebook: Notebook,
    output_path: Path,
    mode: ExportMode = ExportMode.PERCENT,
) -> ExportResult:
    """Export a notebook to a Python module.

    Args:
        notebook: The notebook to export.
        output_path: Path for the output module.
        mode: Export mode (percent or py).

    Returns:
        ExportResult with exported file paths and any warnings.

    Raises:
        ExportError: If the notebook has no exportable cells.
    """
```

### README Updates

Update README.md when adding:
- New CLI commands
- New configuration options
- Breaking changes

---

## Performance Considerations

### CLI Startup

- Use lazy imports in CLI modules
- Avoid heavy computation at import time
- Cache project loading where possible

### Export Performance

- Use notebookx for parsing (Rust-powered)
- Parallelize notebook processing where safe
- Cache parsed notebooks when processing multiple files

---

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.1.0`
4. Push: `git push && git push --tags`
5. CI publishes to PyPI

---

## Quick Reference

### Common Tasks

```bash
# Run tests
pytest

# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy nblite

# Build package
python -m build

# Install locally for development
pip install -e ".[dev]"
```

### Project Links

- notebookx: `/Users/lukastk/dev/20251229_kahguh__notebookx`
- nblite v1: `/Users/lukastk/dev/20250305_000000_YvKoI__nblite`
- Development plan: `PLAN.md`
- Task tracking: `TODO.md`

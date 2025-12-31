# Configuration Guide

nblite is configured through a `nblite.toml` file in your project root. This guide covers all available configuration options.

## Configuration File Location

nblite looks for `nblite.toml` in:
1. The current directory
2. Parent directories (walking up to find the project root)
3. A path specified via `--config` flag or `NBLITE_CONFIG` environment variable

## Complete Configuration Reference

### Top-Level Options

```toml
# Export pipeline definition (required for export)
export_pipeline = "nbs -> lib"

# Documentation code location
docs_cl = "nbs"

# Documentation title
docs_title = "My Project"

# Path to notebook for README generation
readme_nb_path = "nbs/index.ipynb"

# Documentation generator: "mkdocs", "jupyterbook", or "quarto"
docs_generator = "mkdocs"
```

### Export Pipeline

The export pipeline defines how notebooks flow through transformations.

#### String Format (Simple)

```toml
# Single rule
export_pipeline = "nbs -> lib"

# Multiple rules (multiline string)
export_pipeline = """
nbs -> pcts
pcts -> lib
"""
```

#### List Format (Advanced)

```toml
export_pipeline = [
    { from_key = "nbs", to_key = "pcts" },
    { from_key = "pcts", to_key = "lib" },
]
```

#### Pipeline Rules

- Each rule specifies a source (`from_key`) and destination (`to_key`)
- Keys must match defined code locations
- Rules are processed in order
- Cells with `#|export` directives are extracted and written to the destination

---

## Code Locations `[cl.<key>]`

Code locations define directories containing notebooks or modules.

### Basic Definition

```toml
[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.lib]
path = "mylib"
format = "module"
```

### All Options

```toml
[cl.nbs]
# Required: Path relative to project root
path = "nbs"

# Required: Format type
# - "ipynb": Jupyter notebooks (.ipynb)
# - "percent": Percent-style Python (.pct.py)
# - "module": Plain Python modules (.py)
format = "ipynb"

# Optional: Export mode for module format (default: "percent")
# - "percent": Include cell markers (# %% path/to/notebook.ipynb N)
# - "py": Plain Python without cell markers
export_mode = "percent"
```

### Format Details

| Format | File Extension | Description |
|--------|---------------|-------------|
| `ipynb` | `.ipynb` | Full Jupyter notebook with outputs and metadata |
| `percent` | `.pct.py` | Python file with `# %%` cell markers |
| `module` | `.py` | Standard Python module |

### Example: Three-Stage Pipeline

```toml
export_pipeline = """
nbs -> pcts
pcts -> lib
"""

[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pcts]
path = "pcts"
format = "percent"

[cl.lib]
path = "mylib"
format = "module"
export_mode = "py"  # Clean Python without cell markers
```

---

## Git Integration `[git]`

Configure automatic git hooks behavior.

```toml
[git]
# Auto-clean notebooks before commit (default: true)
auto_clean = true

# Run export pipeline on commit (default: true)
auto_export = true

# Validate staging state before commit (default: true)
validate_staging = true
```

### What Each Option Does

| Option | Default | Description |
|--------|---------|-------------|
| `auto_clean` | `true` | Run `nbl clean` before each commit |
| `auto_export` | `true` | Run `nbl export` before each commit |
| `validate_staging` | `true` | Check that notebook twins are staged together |

### Installing Hooks

```bash
nbl install-hooks
```

### Disabling Hooks Temporarily

```bash
NBL_DISABLE_HOOKS=true git commit -m "Skip hooks"
```

---

## Notebook Cleaning `[clean]`

Configure what gets removed when cleaning notebooks.

```toml
[clean]
# Remove all outputs from code cells (default: false)
remove_outputs = false

# Remove execution counts (default: false)
remove_execution_counts = false

# Remove cell-level metadata (default: false)
remove_cell_metadata = false

# Remove notebook-level metadata (default: false)
remove_notebook_metadata = false

# Remove kernel specification (default: false)
remove_kernel_info = false

# Preserve cell IDs (default: true)
preserve_cell_ids = true

# Remove metadata from outputs (default: false)
remove_output_metadata = false

# Remove execution counts from output results (default: false)
remove_output_execution_counts = false

# Keep only specific metadata keys (default: null = keep all)
# keep_only_metadata = ["tags", "name"]

# Skip __* notebooks (default: true)
exclude_dunders = true

# Skip .* notebooks (default: true)
exclude_hidden = true
```

### Common Cleaning Configurations

**Minimal cleaning (for development):**
```toml
[clean]
remove_execution_counts = true
```

**Clean for version control:**
```toml
[clean]
remove_outputs = true
remove_execution_counts = true
```

**Aggressive cleaning:**
```toml
[clean]
remove_outputs = true
remove_execution_counts = true
remove_cell_metadata = true
remove_output_metadata = true
preserve_cell_ids = false
```

---

## Notebook Execution `[fill]`

Configure how notebooks are executed with `nbl fill`.

```toml
[fill]
# Cell execution timeout in seconds (default: null = no timeout)
timeout = null

# Number of parallel workers (default: 4, minimum: 1)
n_workers = 4

# Skip notebooks that haven't changed (default: true)
skip_unchanged = true

# Clear outputs before execution (default: false)
remove_outputs_first = false

# Code locations to fill (default: null = all ipynb locations)
code_locations = null
# code_locations = ["nbs"]

# Glob patterns to exclude
exclude_patterns = []

# Skip __* notebooks (default: true)
exclude_dunders = true

# Skip .* notebooks (default: true)
exclude_hidden = true
```

### Execution Examples

**Fast development (skip unchanged):**
```toml
[fill]
skip_unchanged = true
n_workers = 8
```

**CI/CD (complete execution):**
```toml
[fill]
skip_unchanged = false
timeout = 300  # 5 minute timeout per cell
n_workers = 4
```

**Selective execution:**
```toml
[fill]
code_locations = ["nbs"]  # Only fill notebooks in "nbs" location
exclude_patterns = ["**/scratch_*.ipynb"]
```

---

## Documentation `[docs]`

Configure documentation generation.

```toml
[docs]
# Code location to generate docs from (default: null)
code_location = "nbs"

# Documentation title (default: null)
title = "My Project Documentation"

# Documentation author (default: null)
author = "Your Name"

# Output folder for generated docs (default: "_docs")
output_folder = "_docs"

# Execute notebooks during build (default: false)
execute_notebooks = false

# Patterns to exclude from docs (default: ["__*", ".*"])
exclude_patterns = ["__*", ".*", "**/internal/*"]
```

### Top-Level Docs Options

These are shortcuts for common settings:

```toml
# Shortcut for docs.code_location
docs_cl = "nbs"

# Shortcut for docs.title
docs_title = "My Project"

# Documentation generator to use
docs_generator = "mkdocs"  # or "jupyterbook", "quarto"
```

---

## Export Options `[export]`

Configure export behavior.

```toml
[export]
# Include autogenerated warning in exported files (default: true)
include_autogenerated_warning = true

# Cell reference style in exports (default: "relative")
# - "relative": Path relative to output location
# - "absolute": Full absolute path
cell_reference_style = "relative"
```

### Autogenerated Warning

When `include_autogenerated_warning = true`, exported files start with:

```python
# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/core.ipynb
```

---

## Templates `[templates]`

Configure notebook templates.

```toml
[templates]
# Path to templates folder (default: "templates")
folder = "templates"

# Default template name (default: "default")
default = "default"
```

### Built-in Templates

nblite includes two built-in templates:

**"default"** - Standard notebook template:
```python
# %%
{% if not no_export %}#|default_exp {{ module_name }}{% endif %}

# %% [markdown]
# # {{ title or module_name }}

# %%
#|export
```

**"script"** - For notebooks exported as functions:
```python
# %%
{% if not no_export %}#|default_exp {{ module_name }}
{% endif %}#|export_as_func true

# %%
#|top_export
from pathlib import Path

# %%
#|set_func_signature
def {{ function_name or 'main' }}({{ args or '' }}):
    ...

# %%
#|export
pass
```

### Custom Templates

Create custom templates in your templates folder using Jinja2 syntax. Templates can be written in any notebook format:

```
templates/
├── default.pct.py.jinja    # Percent format template
├── notebook.ipynb.jinja    # ipynb format template
└── custom.py.jinja         # Plain Python (treated as percent)
```

The template format is inferred from the file extension (before `.jinja`), and templates are automatically converted to the output format specified by the notebook path.

### Template Variables

**Built-in variables** (always available):
- `{{ module_name }}` - Module name (from `--name` or inferred from path)
- `{{ title }}` - Notebook title (from `--title`, may be None)
- `{{ no_export }}` - Boolean, true if `--no-export` flag was used
- `{{ pyproject }}` - Contents of `pyproject.toml` as a nested dictionary (if exists)

**Custom variables** can be passed via `--var key=value`:
```bash
nbl new my_notebook.ipynb --var author="John Doe" --var version="1.0"
```

These are then accessible in templates as `{{ author }}` and `{{ version }}`.

### Output Format

The output format is inferred from the notebook path:
- `.ipynb` → Jupyter notebook format
- `.pct.py` → Percent format
- `.py` → Percent format

Templates written in one format are automatically converted to the output format. For example, a template written in percent format (`.pct.py.jinja`) can create an `.ipynb` file.

### Examples

```bash
# Create notebook with default template
nbl new my_notebook.ipynb

# Create percent-format notebook
nbl new my_notebook.pct.py

# Use script template with custom variables
nbl new workflow.ipynb --template script --var function_name=run_pipeline --var args="config: dict"

# Use project data in templates
nbl new my_notebook.ipynb  # {{ pyproject.project.name }} available in template
```

---

## Extensions `[[extensions]]`

Extensions allow you to hook into nblite's workflow and add custom behavior. Extensions are Python files or modules that register callbacks for specific events.

### Configuration

```toml
# Load from file path (relative to project root)
[[extensions]]
path = "nblite_hooks.py"

# Load from Python module
[[extensions]]
module = "mypackage.nblite_extension"
```

Each extension must specify either `path` or `module`, not both. Extensions are loaded when `NbliteProject.from_path()` is called.

### Writing Extensions

Extensions use the `@hook` decorator to register callbacks:

```python
# my_extension.py
from nblite.extensions import hook, HookType

@hook(HookType.PRE_EXPORT)
def before_export(**kwargs):
    """Called before export starts."""
    project = kwargs.get("project")
    print(f"Starting export for {project.root_path}")

@hook(HookType.POST_EXPORT)
def after_export(**kwargs):
    """Called after export completes."""
    result = kwargs.get("result")
    print(f"Created {len(result.files_created)} files")
```

### Available Hooks

| Hook Type | Trigger Point | Context |
|-----------|---------------|---------|
| `PRE_EXPORT` | Before export starts | `project`, `notebooks` |
| `POST_EXPORT` | After export completes | `project`, `result` |
| `PRE_NOTEBOOK_EXPORT` | Before each notebook exports | `notebook`, `output_path`, `from_location`, `to_location` |
| `POST_NOTEBOOK_EXPORT` | After each notebook exports | `notebook`, `output_path`, `from_location`, `to_location`, `success` |
| `PRE_CELL_EXPORT` | Before each cell exports | `cell`, `notebook` |
| `POST_CELL_EXPORT` | After each cell exports | `cell`, `notebook`, `source` |
| `PRE_CLEAN` | Before clean starts | `project`, `notebooks` |
| `POST_CLEAN` | After clean completes | `project`, `cleaned_notebooks` |
| `DIRECTIVE_PARSED` | When a directive is parsed | `directive`, `cell` |

### Example: Custom Logging Extension

```python
# extensions/logging_ext.py
from nblite.extensions import hook, HookType
import logging

logger = logging.getLogger("nblite.custom")

@hook(HookType.PRE_EXPORT)
def log_export_start(**kwargs):
    project = kwargs.get("project")
    logger.info(f"Export starting: {project.root_path}")

@hook(HookType.POST_NOTEBOOK_EXPORT)
def log_notebook_exported(**kwargs):
    nb = kwargs.get("notebook")
    success = kwargs.get("success")
    status = "success" if success else "failed"
    logger.info(f"Notebook {nb.source_path}: {status}")

@hook(HookType.DIRECTIVE_PARSED)
def log_directives(**kwargs):
    directive = kwargs.get("directive")
    logger.debug(f"Found directive: {directive.name}")
```

### Programmatic Hook Registration

You can also register hooks programmatically without the decorator:

```python
from nblite.extensions import HookRegistry, HookType

def my_callback(**kwargs):
    print("Hook triggered!")

HookRegistry.register(HookType.PRE_EXPORT, my_callback)
```

---

## Complete Example Configuration

Here's a comprehensive `nblite.toml` example:

```toml
# nblite configuration for myproject

# Export pipeline: notebooks -> percent scripts -> modules
export_pipeline = """
nbs -> pcts
pcts -> lib
"""

# Documentation
docs_cl = "nbs"
docs_title = "MyProject Documentation"
docs_generator = "mkdocs"
readme_nb_path = "nbs/00_index.ipynb"

# Code locations
[cl.nbs]
path = "nbs"
format = "ipynb"

[cl.pcts]
path = "pcts"
format = "percent"

[cl.lib]
path = "myproject"
format = "module"
export_mode = "percent"

# Export options
[export]
include_autogenerated_warning = true
cell_reference_style = "relative"

# Git integration
[git]
auto_clean = true
auto_export = true
validate_staging = true

# Notebook cleaning
[clean]
remove_outputs = false
remove_execution_counts = true
preserve_cell_ids = true
exclude_dunders = true
exclude_hidden = true

# Notebook execution
[fill]
timeout = 300
n_workers = 4
skip_unchanged = true
exclude_dunders = true
exclude_hidden = true

# Documentation generation
[docs]
code_location = "nbs"
title = "MyProject Documentation"
author = "Your Name"
output_folder = "_docs"
execute_notebooks = false
exclude_patterns = ["__*", ".*", "**/scratch_*"]

# Templates
[templates]
folder = "templates"
default = "default"
```

---

## Environment Variables

nblite respects these environment variables:

| Variable | Description |
|----------|-------------|
| `NBLITE_CONFIG` | Path to `nblite.toml` config file |
| `NBLITE_DISABLE_EXPORT` | Set to `true` to disable `nbl_export()` in notebooks |
| `NBL_DISABLE_HOOKS` | Set to `true` to skip git hooks |

---

## Configuration Precedence

When options can be set in multiple places:

1. **CLI flags** (highest priority)
2. **Environment variables**
3. **nblite.toml configuration**
4. **Default values** (lowest priority)

Example:
```bash
# CLI flag overrides config file
nbl fill --workers 8  # Uses 8 workers even if config says 4
```

# CLI Reference

Complete reference for all nblite CLI commands.

## Global Options

These options are available for all commands:

```bash
nbl --config/-c PATH    # Path to nblite.toml config file
nbl --version/-v        # Show version and exit
nbl --help              # Show help message
```

The config path can also be set via the `NBLITE_CONFIG` environment variable.

---

## Project Management

### `nbl init`

Initialize a new nblite project.

```bash
nbl init [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Module name (default: directory name) |
| `--path` | `-p` | Project path (default: current directory) |
| `--use-defaults` | | Use defaults without prompting |

**Examples:**

```bash
# Initialize in current directory
nbl init

# Initialize with specific name
nbl init --name mylib

# Initialize in different directory
nbl init --path ~/projects/mylib --name mylib
```

**Output:**

Creates:
- `nblite.toml` - Configuration file
- `nbs/` - Notebooks directory
- `<name>/` - Python package directory with `__init__.py`

---

### `nbl new`

Create a new notebook from a template.

```bash
nbl new NOTEBOOK_PATH [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NOTEBOOK_PATH` | Path for the new notebook |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Module name for `#\|default_exp` directive |
| `--title` | `-t` | Notebook title (creates markdown cell) |
| `--template` | | Template to use (name, path, or built-in: "default", "script") |
| `--no-export` | | Don't include `#\|default_exp` directive |
| `--var` | `-v` | Template variable as `key=value` (can be repeated) |

**Output format:**

The output format is inferred from the notebook path:
- `.ipynb` → Jupyter notebook format
- `.pct.py` → Percent format
- `.py` → Percent format

**Examples:**

```bash
# Create ipynb notebook with automatic module name
nbl new nbs/utils.ipynb

# Create percent-format notebook
nbl new nbs/utils.pct.py

# Create notebook with title
nbl new nbs/core.ipynb --title "Core Module"

# Create notebook with specific module name
nbl new nbs/helpers.ipynb --name mylib.helpers

# Create notebook without export directive
nbl new nbs/scratch.ipynb --no-export

# Use script template with custom variables
nbl new nbs/workflow.ipynb --template script --var function_name=run_pipeline --var args="config: dict"

# Pass multiple custom variables
nbl new nbs/app.ipynb --var author="John Doe" --var version="1.0"

# Use a custom template file
nbl new nbs/custom.ipynb --template templates/my_template.pct.py.jinja
```

**Template variables:**

Built-in variables available in all templates:
- `module_name` - Module name (from `--name` or inferred from path)
- `title` - Notebook title (from `--title`)
- `no_export` - Boolean, true if `--no-export` was used
- `pyproject` - Contents of `pyproject.toml` as a nested dict (if exists)

Custom variables can be passed via `--var key=value` and used as `{{ key }}` in templates.

---

### `nbl info`

Show project information.

```bash
nbl info
```

**Output:**

Displays:
- Project root path
- Code locations with paths, formats, and file counts
- Export pipeline rules

**Example output:**

```
Project: /home/user/myproject

        Code Locations
┏━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┓
┃ Key  ┃ Path     ┃ Format ┃ Files ┃
┡━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━┩
│ nbs  │ nbs      │ ipynb  │ 5     │
│ lib  │ mylib    │ module │ 5     │
└──────┴──────────┴────────┴───────┘

Export Pipeline:
  nbs -> lib
```

---

### `nbl list`

List notebooks and files in code locations.

```bash
nbl list [CODE_LOCATION]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `CODE_LOCATION` | Code location to list (optional, all if omitted) |

**Examples:**

```bash
# List all code locations
nbl list

# List specific code location
nbl list nbs
```

---

## Export and Conversion

### `nbl export`

Run the export pipeline.

```bash
nbl export [NOTEBOOKS...] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NOTEBOOKS` | Specific notebooks to export (optional, all if omitted) |

**Options:**

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be exported without doing it |
| `--export-pipeline` | Custom export pipeline (overrides config) |

**Examples:**

```bash
# Export all notebooks
nbl export

# Export specific notebooks
nbl export nbs/core.ipynb nbs/utils.ipynb

# Preview export without changes
nbl export --dry-run

# Use custom pipeline
nbl export --export-pipeline "nbs -> lib"

# Multiple rules (comma-separated)
nbl export --export-pipeline "nbs -> pts, pts -> lib"

# Reverse direction (percent to ipynb)
nbl export --export-pipeline "pts -> nbs"
```

The `--export-pipeline` option allows you to override the pipeline defined in `nblite.toml`. This is useful for:
- Running a subset of the pipeline
- Reversing the export direction (e.g., converting percent files back to ipynb)
- Testing different pipeline configurations

---

### `nbl convert`

Convert notebook between formats.

```bash
nbl convert INPUT_PATH OUTPUT_PATH [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INPUT_PATH` | Input notebook path |
| `OUTPUT_PATH` | Output notebook path |

**Options:**

| Option | Description |
|--------|-------------|
| `--from` | Input format (auto-detected if omitted) |
| `--to` | Output format (auto-detected if omitted) |

**Supported formats:** `ipynb`, `percent`

**Examples:**

```bash
# Convert ipynb to percent format
nbl convert notebook.ipynb notebook.pct.py

# Convert percent to ipynb
nbl convert script.pct.py notebook.ipynb

# Explicit format specification
nbl convert input.txt output.txt --from percent --to ipynb
```

---

### `nbl from-module`

Convert Python module(s) to notebook(s).

```bash
nbl from-module INPUT_PATH OUTPUT_PATH [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INPUT_PATH` | Path to Python file or directory |
| `OUTPUT_PATH` | Output notebook path or directory |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Module name for `#\|default_exp` (single file only) |
| `--format` | `-f` | Output format: `ipynb` (default) or `percent` |
| `--recursive` | `-r` | Process subdirectories recursively (default: true) |
| `--include-init` | | Include `__init__.py` files |
| `--include-dunders` | | Include `__*.py` files |
| `--include-hidden` | | Include hidden files/directories |

**Examples:**

```bash
# Convert single file
nbl from-module utils.py nbs/utils.ipynb

# Convert with custom module name
nbl from-module lib/core.py nbs/core.ipynb --name mylib.core

# Convert entire directory
nbl from-module src/ nbs/ --recursive

# Convert to percent format
nbl from-module src/ pcts/ --format percent

# Include __init__.py files
nbl from-module mypackage/ nbs/ --include-init
```

**Behavior:**

For single files, creates a notebook with:
- `#|default_exp` directive
- Code cells for imports (with `#|export`)
- Code cells for each function/class (with `#|export`)
- Markdown cells for module docstrings

For directories:
- Recursively processes all `.py` files
- Preserves directory structure
- Module names derived from paths (e.g., `sub/utils.py` → `sub.utils`)

---

## Notebook Operations

### `nbl clean`

Clean notebooks by removing outputs and metadata.

```bash
nbl clean [NOTEBOOKS...] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NOTEBOOKS` | Specific notebooks to clean (optional, all if omitted) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--remove-outputs` | `-O` | Remove all outputs from code cells |
| `--remove-execution-counts` | `-e` | Remove execution counts |
| `--remove-cell-metadata` | | Remove cell-level metadata |
| `--remove-notebook-metadata` | | Remove notebook-level metadata |
| `--remove-kernel-info` | | Remove kernel specification |
| `--preserve-cell-ids` | | Preserve cell IDs (default: true) |
| `--remove-cell-ids` | | Remove cell IDs |
| `--remove-output-metadata` | | Remove metadata from outputs |
| `--remove-output-execution-counts` | | Remove execution counts from outputs |
| `--keep-only` | | Keep only specific metadata keys (comma-separated) |

**Examples:**

```bash
# Remove outputs only
nbl clean -O

# Remove outputs and execution counts
nbl clean -O -e

# Clean specific notebooks
nbl clean nbs/core.ipynb nbs/utils.ipynb -O

# Aggressive cleaning
nbl clean -O -e --remove-cell-metadata --remove-cell-ids

# Keep only specific metadata
nbl clean --keep-only tags,name
```

---

### `nbl fill`

Execute notebooks and fill cell outputs.

```bash
nbl fill [NOTEBOOKS...] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NOTEBOOKS` | Specific notebooks to fill (optional, all ipynb if omitted) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--code-location` | `-c` | Code locations to fill (can repeat) |
| `--timeout` | `-t` | Cell execution timeout in seconds |
| `--workers` | `-w` | Number of parallel workers (default: 4) |
| `--fill-unchanged` | | Fill notebooks even if unchanged |
| `--remove-outputs` | | Clear outputs before execution |
| `--include-dunders` | | Include `__*` notebooks |
| `--include-hidden` | | Include `.*` notebooks |
| `--dry-run` | `-n` | Execute without saving results |
| `--silent` | `-s` | Suppress progress output |
| `--allow-export` | | Allow `nbl_export()` during fill (disabled by default) |

**Examples:**

```bash
# Fill all notebooks
nbl fill

# Fill specific notebooks
nbl fill nbs/core.ipynb nbs/utils.ipynb

# Fill with more workers
nbl fill --workers 8

# Fill with timeout
nbl fill --timeout 60

# Force fill unchanged notebooks
nbl fill --fill-unchanged

# Clear outputs first
nbl fill --remove-outputs

# Dry run (test execution)
nbl fill --dry-run

# Silent mode (for CI)
nbl fill --silent

# Allow nbl_export() during fill
nbl fill --allow-export
```

**Export behavior:**

By default, `nbl_export()` calls in notebooks are disabled during fill to prevent interference with notebook execution. Use `--allow-export` to enable them if needed.

**Change detection:**

By default, nblite tracks notebook changes using a hash. Unchanged notebooks are skipped. Use `--fill-unchanged` to override.

---

### `nbl test`

Test that notebooks execute without errors (dry run mode).

```bash
nbl test [NOTEBOOKS...] [OPTIONS]
```

This is equivalent to `nbl fill --dry-run`. Same options as `fill` except:
- Always runs in dry-run mode (doesn't save outputs)
- No `--remove-outputs` option

By default, `nbl_export()` calls in notebooks are disabled during test to prevent interference. Use `--allow-export` to enable them if needed.

**Examples:**

```bash
# Test all notebooks
nbl test

# Test with timeout
nbl test --timeout 120

# Test silently (for CI)
nbl test --silent
```

---

## Documentation

### `nbl readme`

Generate README.md from a notebook.

```bash
nbl readme [NOTEBOOK_PATH] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NOTEBOOK_PATH` | Path to notebook (uses `readme_nb_path` config if omitted) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output path (default: README.md in project root) |

**Examples:**

```bash
# Use configured readme_nb_path
nbl readme

# Specify notebook
nbl readme nbs/index.ipynb

# Custom output
nbl readme nbs/index.ipynb -o docs/README.md
```

**Behavior:**

- Converts notebook to markdown
- Filters out cells with `#|hide` directive
- Respects `#|hide_input` and `#|hide_output` directives

---

### `nbl render-docs`

Render documentation for the project.

```bash
nbl render-docs [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output folder (default: `_docs`) |
| `--generator` | `-g` | Generator: `mkdocs`, `jupyterbook`, or `quarto` |
| `--docs-cl` | `-d` | Code location to generate docs from |

**Examples:**

```bash
# Build with default generator
nbl render-docs

# Build with specific generator
nbl render-docs -g quarto

# Custom output folder
nbl render-docs -o docs_output

# Specify code location
nbl render-docs -d nbs
```

**Requirements:**

| Generator | Installation |
|-----------|-------------|
| mkdocs | `pip install mkdocs mkdocs-material mkdocs-jupyter` |
| jupyterbook | `pip install jupyter-book` |
| quarto | Install from https://quarto.org/ |

---

### `nbl preview-docs`

Preview documentation with live reload.

```bash
nbl preview-docs [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--generator` | `-g` | Generator: `mkdocs`, `jupyterbook`, or `quarto` |
| `--docs-cl` | `-d` | Code location to generate docs from |

**Examples:**

```bash
# Preview with default generator
nbl preview-docs

# Preview with specific generator
nbl preview-docs -g jupyterbook
```

Press `Ctrl+C` to stop the preview server.

---

## Workflow Commands

### `nbl prepare`

Run export, clean, fill, and readme in sequence.

```bash
nbl prepare [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--skip-export` | Skip export step |
| `--skip-clean` | Skip clean step |
| `--skip-fill` | Skip fill step |
| `--skip-readme` | Skip readme step |
| `--clean-outputs` | Remove outputs during clean |
| `--fill-workers` / `-w` | Number of fill workers (default: 4) |
| `--fill-unchanged` | Fill notebooks even if unchanged |

**Examples:**

```bash
# Full preparation
nbl prepare

# Skip fill (faster)
nbl prepare --skip-fill

# Clean outputs
nbl prepare --clean-outputs

# More fill workers
nbl prepare --fill-workers 8
```

**Sequence:**

1. **Export** - Run export pipeline
2. **Clean** - Clean notebooks
3. **Fill** - Execute notebooks and save outputs
4. **README** - Generate README (if `readme_nb_path` configured)

---

## Git Integration

### `nbl install-hooks`

Install git hooks for the project.

```bash
nbl install-hooks
```

Installs a pre-commit hook that:
1. Cleans notebooks (if `git.auto_clean = true`)
2. Runs export (if `git.auto_export = true`)
3. Validates staging (if `git.validate_staging = true`)

---

### `nbl uninstall-hooks`

Remove git hooks for the project.

```bash
nbl uninstall-hooks
```

---

### `nbl validate`

Validate git staging state.

```bash
nbl validate
```

**Checks:**
- Notebooks don't have uncommitted outputs (if configured)
- Notebook twins are staged together
- Exports are up to date

**Output:**
- Warnings for potential issues
- Errors that would block commit

---

### `nbl hook`

Run a git hook (internal use).

```bash
nbl hook HOOK_NAME
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `HOOK_NAME` | Hook name: `pre-commit`, `post-commit` |

This command is called by git hooks and not intended for direct use.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (see error message) |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NBLITE_CONFIG` | Path to `nblite.toml` config file |
| `NBLITE_DISABLE_EXPORT` | Disable `nbl_export()` function (set to `true`) |
| `NBL_DISABLE_HOOKS` | Skip git hooks (set to `true`) |

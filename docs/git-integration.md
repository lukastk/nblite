# Git Integration

nblite integrates with Git to automate notebook cleaning, export, and validation. This guide covers setup and best practices.

## Overview

nblite's Git integration provides:
- **Pre-commit hooks**: Automatically clean and export before commits
- **Staging validation**: Ensure notebooks and exports are committed together
- **Clean workflows**: Keep repository history clean

## Installing Git Hooks

Install hooks with:

```bash
nbl install-hooks
```

This creates a pre-commit hook in `.git/hooks/` that runs nblite commands before each commit.

## Hook Configuration

Configure hook behavior in `nblite.toml`:

```toml
[git]
# Clean notebooks before commit
auto_clean = true

# Run export pipeline before commit
auto_export = true

# Validate staging state
validate_staging = true
```

### `auto_clean`

When `true`, runs notebook cleaning before commit:

```bash
nbl clean
```

Uses settings from `[clean]` section:

```toml
[clean]
remove_outputs = false
remove_execution_counts = true
```

### `auto_export`

When `true`, runs the export pipeline before commit:

```bash
nbl export
```

This ensures Python modules are always up-to-date with notebooks.

### `validate_staging`

When `true`, checks staging state:

- Warns if notebooks have outputs but `remove_outputs = false`
- Errors if notebook twins aren't staged together
- Ensures consistency between notebooks and exports

## Pre-Commit Hook Behavior

The pre-commit hook runs these steps in order:

1. **Auto-clean** (if enabled)
   - Cleans notebooks according to config
   - Re-stages cleaned notebooks

2. **Auto-export** (if enabled)
   - Runs export pipeline
   - Re-stages generated files

3. **Validate staging** (if enabled)
   - Checks for inconsistencies
   - Blocks commit on errors

## Removing Hooks

Remove hooks with:

```bash
nbl uninstall-hooks
```

## Bypassing Hooks

Temporarily skip hooks:

```bash
# Using environment variable
NBL_DISABLE_HOOKS=true git commit -m "Emergency fix"

# Using git flag (skips all hooks)
git commit --no-verify -m "Skip all hooks"
```

## Manual Validation

Run validation manually:

```bash
nbl validate
```

**Example output:**

```
Warning: nbs/core.ipynb has outputs but remove_outputs is disabled
Staging is valid
```

Or with errors:

```
Error: nbs/core.ipynb is staged but mylib/core.py is not
Error: Run 'nbl export' and stage the generated files
```

## Recommended Workflow

### Development Workflow

1. **Edit notebooks** in Jupyter
2. **Test interactively** in the notebook
3. **Run export** to update modules:
   ```bash
   nbl export
   ```
4. **Fill outputs** (optional):
   ```bash
   nbl fill
   ```
5. **Commit changes**:
   ```bash
   git add nbs/ mylib/
   git commit -m "Add feature X"
   ```

With hooks enabled, steps 3-4 happen automatically on commit.

### Team Workflow

For teams, use consistent hook configuration:

```toml
# nblite.toml - commit this to the repo
[git]
auto_clean = true
auto_export = true
validate_staging = true

[clean]
remove_outputs = true       # Keep notebooks clean in repo
remove_execution_counts = true
```

Each team member runs:

```bash
nbl install-hooks
```

### CI/CD Workflow

In CI, verify notebooks are consistent:

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install nblite

      - name: Validate notebooks
        run: nbl validate

      - name: Test notebooks execute
        run: nbl test --silent

      - name: Check exports are up to date
        run: |
          nbl export
          git diff --exit-code
```

## Notebook Twins

"Twins" are related files that should be committed together:

| Notebook | Twin(s) |
|----------|---------|
| `nbs/core.ipynb` | `mylib/core.py`, `pcts/core.pct.py` |

When you modify a notebook, its exported modules change too. Staging validation ensures you don't accidentally commit one without the other.

## Common Scenarios

### Scenario 1: Quick Fix to Module

Sometimes you need to fix the Python module directly:

1. Edit `mylib/core.py`
2. Update the corresponding notebook
3. Commit both

Or, edit the notebook and let auto-export regenerate the module.

### Scenario 2: Exploratory Work

For exploration that shouldn't be committed:

```python
#|eval: false
# This won't run during fill
experimental_code()
```

Or use a separate notebook:

```
nbs/
├── core.ipynb           # Production
└── core_scratch.ipynb   # Exploration (add to .gitignore)
```

### Scenario 3: Large Refactoring

When refactoring across multiple notebooks:

1. Disable hooks temporarily:
   ```bash
   export NBL_DISABLE_HOOKS=true
   ```

2. Make all changes

3. Re-enable and validate:
   ```bash
   unset NBL_DISABLE_HOOKS
   nbl export
   nbl validate
   ```

4. Commit everything together

## .gitignore Recommendations

```gitignore
# Ignore scratch notebooks
*_scratch.ipynb
scratch_*.ipynb

# Ignore notebook checkpoints
.ipynb_checkpoints/

# Ignore generated documentation
_docs/

# Keep these in version control:
# - nbs/*.ipynb (source notebooks)
# - mylib/*.py (generated modules)
# - pcts/*.pct.py (if using intermediate format)
```

## Outputs in Version Control

### Option 1: Remove Outputs (Recommended)

```toml
[clean]
remove_outputs = true
```

**Pros:**
- Smaller repository
- Clean diffs
- No merge conflicts in outputs

**Cons:**
- Outputs must be regenerated locally
- No visual outputs in GitHub preview

### Option 2: Keep Outputs

```toml
[clean]
remove_outputs = false
```

**Pros:**
- Outputs visible in GitHub
- No need to run notebooks locally

**Cons:**
- Larger repository
- Noisy diffs
- Potential merge conflicts

### Option 3: Hybrid Approach

Keep outputs in main notebooks, remove from internal ones:

```bash
# Clean specific notebooks
nbl clean -O nbs/internal/*.ipynb
```

## Troubleshooting

### Hook Not Running

1. Check hook is installed:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. Check hook is executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. Reinstall:
   ```bash
   nbl uninstall-hooks
   nbl install-hooks
   ```

### "Not in a git repository"

Hooks only work in Git repositories:

```bash
git init
nbl install-hooks
```

### Validation Errors

**"Notebook X is staged but module Y is not"**

Run export and stage the generated files:

```bash
nbl export
git add mylib/
git commit
```

**"Notebook has outputs but remove_outputs is disabled"**

Either:
- Enable `remove_outputs = true` in config
- Clean manually: `nbl clean -O`
- Accept the warning (it's just a warning)

### Hooks Too Slow

If hooks are slow:

1. Reduce what's cleaned:
   ```toml
   [clean]
   remove_outputs = false  # Faster than removing
   ```

2. Disable auto-fill (if enabled):
   ```toml
   [git]
   auto_fill = false
   ```

3. Limit to changed files:
   ```bash
   # Manual workflow
   nbl export nbs/changed_file.ipynb
   ```

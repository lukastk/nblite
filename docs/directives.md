# Directives Reference

Directives are special comments in notebook cells that control nblite's behavior. They follow the format `#|directive_name value`.

## Overview

Directives are processed during:
- **Export**: Determine what code goes to modules
- **Fill**: Control which cells execute
- **Documentation**: Control visibility in generated docs

## Directive Syntax

### Basic Syntax

```python
#|directive_name value
```

### Rules

1. **Placement**: Most directives must be at the top of the cell (topmatter)
2. **Multiple directives**: Can have multiple directives per cell
3. **Case sensitive**: Directive names are case-sensitive
4. **Continuation**: Use backslash for multi-line values

**Valid:**
```python
#|export
#|hide
def my_function():
    pass
```

**Invalid:**
```python
def my_function():
    pass
#|export  # ERROR: directive after code
```

---

## Export Directives

These directives control what gets exported to Python modules.

### `#|default_exp`

Set the default export module for the notebook.

**Syntax:**
```python
#|default_exp module_name
```

**Location:** Must be in a cell by itself, typically the first code cell.

**Examples:**
```python
#|default_exp core

#|default_exp mylib.utils

#|default_exp mylib.io.readers
```

**Behavior:**
- Sets the target module for `#|export` directives
- Module path is relative to the output code location
- Creates nested directories as needed

---

### `#|export`

Export this cell to the default module.

**Syntax:**
```python
#|export
```

**Location:** Topmatter (top of cell)

**Example:**
```python
#|export
def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"
```

**Behavior:**
- Cell content is exported to the module set by `#|default_exp`
- Function/class names are automatically added to `__all__`
- The directive is stripped from the exported code

---

### `#|exporti`

Export as internal (not included in `__all__`).

**Syntax:**
```python
#|exporti
```

**Location:** Topmatter

**Example:**
```python
#|exporti
def _internal_helper():
    """Internal function not exposed in public API."""
    pass
```

**Behavior:**
- Exports the cell but doesn't add names to `__all__`
- Useful for internal/private functions

---

### `#|export_to`

Export to a specific module (override default).

**Syntax:**
```python
#|export_to module_name [ORDER]
```

**Location:** Topmatter

**Arguments:**
- `module_name`: Target module path
- `ORDER`: Optional integer for ordering exports (lower = earlier)

**Examples:**
```python
#|export_to mylib.helpers
def helper_function():
    pass

#|export_to mylib.core 10
# This appears early in the module due to ORDER=10
CONSTANT = 42
```

**Behavior:**
- Exports to the specified module instead of the default
- Multiple cells can export to the same module
- ORDER controls the position in the output file

---

## Function Export Directives

These directives are used with `#|export_as_func` to export notebooks as callable functions.

### `#|export_as_func`

Export the notebook as a single callable function.

**Syntax:**
```python
#|export_as_func true
```

**Location:** Topmatter, typically with `#|default_exp`

**Example:**
```python
#|default_exp workflows.process
#|export_as_func true
```

**Behavior:**
- The entire notebook becomes a function body
- Combined with other function directives below

---

### `#|set_func_signature`

Define the function signature.

**Syntax:**
```python
#|set_func_signature
def function_name(arg1: Type, arg2: Type) -> ReturnType:
    ...
```

**Location:** Topmatter

**Example:**
```python
#|set_func_signature
def process_data(input_path: str, output_path: str) -> dict:
    ...
```

**Behavior:**
- Defines the function name, parameters, and return type
- The `...` is a placeholder (function body comes from other cells)

---

### `#|top_export`

Code placed at module level, before the function.

**Syntax:**
```python
#|top_export
```

**Location:** Topmatter

**Example:**
```python
#|top_export
import pandas as pd
from pathlib import Path

CHUNK_SIZE = 1000
```

**Behavior:**
- Code appears outside the function
- Use for imports and constants needed by the function

---

### `#|func_return`

Prepend `return` to the first line of the cell.

**Syntax:**
```python
#|func_return
```

**Location:** Topmatter

**Example:**
```python
#|func_return
{"status": "success", "count": len(results)}
```

**Becomes:**
```python
return {"status": "success", "count": len(results)}
```

---

### `#|func_return_line`

Prepend `return` to a specific line (inline directive).

**Syntax:**
```python
expression  #|func_return_line
```

**Location:** Inline (after code on same line)

**Example:**
```python
result = process(data)
result  #|func_return_line
```

**Becomes:**
```python
result = process(data)
return result
```

---

## Documentation Directives

These directives control how cells appear in generated documentation.

### `#|hide`

Hide the entire cell from documentation.

**Syntax:**
```python
#|hide
```

**Location:** Topmatter

**Example:**
```python
#|hide
# This cell won't appear in documentation
import internal_module
setup_environment()
```

**Behavior:**
- Cell is completely excluded from documentation output
- Cell still executes normally
- Useful for setup code, internal imports, etc.

---

### `#|hide_input`

Show only the output, hide the code.

**Syntax:**
```python
#|hide_input
```

**Location:** Topmatter

**Example:**
```python
#|hide_input
# Code is hidden, but the plot appears in docs
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [1, 4, 9])
plt.show()
```

**Behavior:**
- Code is hidden from documentation
- Output (plots, tables, etc.) is shown
- Useful for visualization cells where code isn't educational

---

### `#|hide_output`

Show only the code, hide the output.

**Syntax:**
```python
#|hide_output
```

**Location:** Topmatter

**Example:**
```python
#|hide_output
# Code is shown, but verbose output is hidden
model.fit(X_train, y_train, verbose=1)
```

**Behavior:**
- Code is shown in documentation
- Output is hidden
- Useful when output is verbose or not relevant

---

## Execution Control Directives

These directives control cell execution during `nbl fill` and `nbl test`.

### `#|eval`

Control whether a cell is executed.

**Syntax:**
```python
#|eval: false
```

**Location:** Topmatter

**Example:**
```python
#|eval: false
# This cell is skipped during fill/test
long_running_computation()
```

**Values:**
- `true` (default): Execute the cell
- `false`: Skip the cell

---

### `#|skip_evals`

Skip this cell and all following cells.

**Syntax:**
```python
#|skip_evals
```

**Location:** Topmatter

**Example:**
```python
#|skip_evals
# All cells from here are skipped
expensive_training()

# This cell is also skipped
evaluate_model()
```

**Behavior:**
- Skips the current cell
- Skips all subsequent cells
- Until `#|skip_evals_stop` is encountered

---

### `#|skip_evals_stop`

Resume execution after `#|skip_evals`.

**Syntax:**
```python
#|skip_evals_stop
```

**Location:** Topmatter

**Example:**
```python
#|skip_evals
# Skipped during automated execution
interactive_exploration()

#|skip_evals_stop
# Execution resumes here
print("Back to normal execution")
```

**Behavior:**
- Marks the end of a skip region
- Cell with this directive IS executed
- Subsequent cells execute normally

---

## Complete Example

Here's a notebook demonstrating various directives:

**Cell 1:**
```python
#|default_exp mylib.utils
```

**Cell 2 (markdown):**
```markdown
# Utility Functions

This module provides utility functions for data processing.
```

**Cell 3:**
```python
#|export
import pandas as pd
from pathlib import Path
```

**Cell 4:**
```python
#|hide
# Setup for documentation examples
sample_data = pd.DataFrame({"a": [1, 2, 3]})
```

**Cell 5:**
```python
#|export
def load_csv(path: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Args:
        path: Path to the CSV file

    Returns:
        DataFrame with the CSV contents
    """
    return pd.read_csv(path)
```

**Cell 6:**
```python
# Test the function (not exported)
df = load_csv("sample.csv")
df.head()
```

**Cell 7:**
```python
#|exporti
def _validate_path(path: str) -> Path:
    """Internal validation function."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return p
```

**Cell 8:**
```python
#|hide_input
# Show a nice visualization
df.plot(kind='bar')
```

**Cell 9:**
```python
#|skip_evals
# Skip expensive computation during automated testing
full_analysis = run_expensive_analysis(large_dataset)
```

**Cell 10:**
```python
#|skip_evals_stop
print("Notebook complete!")
```

---

## Directive Quick Reference

### Export

| Directive | Description |
|-----------|-------------|
| `#\|default_exp module` | Set default export module |
| `#\|export` | Export to default module |
| `#\|exporti` | Export as internal (not in `__all__`) |
| `#\|export_to module [ORDER]` | Export to specific module |

### Function Export

| Directive | Description |
|-----------|-------------|
| `#\|export_as_func true` | Export notebook as function |
| `#\|set_func_signature` | Define function signature |
| `#\|top_export` | Code at module level |
| `#\|func_return` | Prepend return to first line |
| `#\|func_return_line` | Prepend return (inline) |

### Documentation

| Directive | Description |
|-----------|-------------|
| `#\|hide` | Hide entire cell |
| `#\|hide_input` | Hide code, show output |
| `#\|hide_output` | Show code, hide output |

### Execution

| Directive | Description |
|-----------|-------------|
| `#\|eval: false` | Skip cell execution |
| `#\|skip_evals` | Skip remaining cells |
| `#\|skip_evals_stop` | Resume execution |

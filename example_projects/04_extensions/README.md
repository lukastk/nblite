# Extensions Example

This example demonstrates the nblite hook/extension system.

## Hook Types

| Hook | When Triggered |
|------|----------------|
| `PRE_EXPORT` | Before export starts |
| `POST_EXPORT` | After export completes |
| `PRE_NOTEBOOK_EXPORT` | Before each notebook is exported |
| `POST_NOTEBOOK_EXPORT` | After each notebook is exported |
| `PRE_CELL_EXPORT` | Before each cell is exported |
| `POST_CELL_EXPORT` | After each cell is exported |
| `PRE_CLEAN` | Before clean starts |
| `POST_CLEAN` | After clean completes |
| `DIRECTIVE_PARSED` | When a directive is parsed |

## Configuration

```toml
# Load extension from file path
[[extensions]]
path = "nblite_ext.py"

# Or load from a Python module
[[extensions]]
module = "mypackage.nblite_extension"
```

## Writing Extensions

```python
from nblite.extensions import HookType, hook

@hook(HookType.PRE_EXPORT)
def before_export(project, notebooks, **kwargs):
    print(f"Exporting from {project.root_path}")

@hook(HookType.POST_NOTEBOOK_EXPORT)
def after_notebook(notebook, output_path, success, **kwargs):
    if success:
        print(f"Exported: {output_path}")
```

## Run the Example

```bash
./run_example.sh
```

Watch for `[EXT]` prefixed messages to see the extension in action.

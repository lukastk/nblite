# Export Modes Example

This example demonstrates the difference between `percent` and `py` export modes.

## Export Modes

- **`percent`** (default): Exported `.py` files include cell markers like `# %% ../nbs/utils.ipynb`
- **`py`**: Clean Python without any cell references or markers

## Configuration

```toml
[cl.lib_percent]
path = "mypackage_percent"
format = "module"
export_mode = "percent"

[cl.lib_plain]
path = "mypackage_plain"
format = "module"
export_mode = "py"
```

## Run the Example

```bash
./run_example.sh
```

This will export the notebooks and show the difference between the two export modes.

# Clean Options Example

This example demonstrates various notebook cleaning configurations.

## Configuration Options

```toml
[clean]
remove_outputs = true               # Remove cell outputs
remove_execution_counts = true      # Remove [1], [2], etc.
remove_cell_metadata = false        # Keep cell metadata
remove_notebook_metadata = false    # Keep notebook metadata
remove_kernel_info = false          # Keep kernel info
preserve_cell_ids = true            # Keep cell IDs for stable diffs
remove_output_metadata = true       # Clean output metadata
remove_output_execution_counts = true
exclude_dunders = true              # Skip __*.ipynb files
exclude_hidden = true               # Skip .*.ipynb files
```

## Options Explained

| Option | Description |
|--------|-------------|
| `remove_outputs` | Remove all cell outputs (stdout, stderr, display data) |
| `remove_execution_counts` | Remove the `[1]`, `[2]` numbers from cells |
| `remove_cell_metadata` | Remove metadata from individual cells |
| `remove_notebook_metadata` | Remove notebook-level metadata |
| `remove_kernel_info` | Remove kernel specification |
| `preserve_cell_ids` | Keep cell IDs (helps with git diffs) |
| `remove_output_metadata` | Remove metadata from output results |
| `remove_output_execution_counts` | Remove execution counts from outputs |

## Run the Example

```bash
./run_example.sh
```

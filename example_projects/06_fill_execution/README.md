# Fill Execution Example

This example demonstrates notebook execution with `nbl fill`.

## Configuration

```toml
[fill]
timeout = 60                       # Timeout per cell in seconds
n_workers = 2                      # Parallel execution workers
skip_unchanged = true              # Skip unchanged notebooks
remove_outputs_first = false       # Clear outputs before running
code_locations = ["nbs"]           # Which locations to fill
exclude_patterns = ["scratch/*"]   # Patterns to exclude
exclude_dunders = true
exclude_hidden = true
```

## Commands

- `nbl fill` - Execute notebooks and save outputs
- `nbl test` - Dry-run execution (don't save)

## Options Explained

| Option | Description |
|--------|-------------|
| `timeout` | Maximum seconds per cell (None = unlimited) |
| `n_workers` | Number of parallel notebook executions |
| `skip_unchanged` | Skip notebooks whose source hasn't changed |
| `remove_outputs_first` | Clear existing outputs before execution |
| `code_locations` | List of code locations to fill |
| `exclude_patterns` | Glob patterns to exclude |

## Run the Example

```bash
./run_example.sh
```

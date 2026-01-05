# From Module Example

This example demonstrates converting existing Python modules to notebooks using `nbl from-module`.

## Use Cases

- Migrating existing Python packages to nblite
- Converting scripts to notebooks for interactive development
- Creating notebook versions of existing modules

## Commands

```bash
# Convert a single file
nbl from-module src/utils.py nbs/utils.ipynb

# Convert an entire directory
nbl from-module src/ nbs/ --recursive

# Convert to percent format instead
nbl from-module src/utils.py nbs/utils.pct.py --format percent
```

## Options

| Option | Description |
|--------|-------------|
| `--name, -n` | Module name for default_exp (single file only) |
| `--format, -f` | Output format: `ipynb` (default) or `percent` |
| `--recursive, -r` | Process subdirectories recursively |
| `--include-init` | Include `__init__.py` files |
| `--include-dunders` | Include `__*.py` files |
| `--include-hidden` | Include hidden files/directories |

## Run the Example

```bash
./run_example.sh
```

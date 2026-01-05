# Multi-Pipeline Example

This example demonstrates complex multi-branch export pipelines.

## Pipeline Structure

```
nbs ──┬──> pcts ──> lib_alt (export_mode = py)
      │
      └──> lib (export_mode = percent)
```

## Configuration

```toml
export_pipeline = """
nbs -> pcts
nbs -> lib
pcts -> lib_alt
"""
```

This creates:
- `nbs/` - Source notebooks (ipynb)
- `pcts/` - Percent format scripts (intermediate)
- `mypackage/` - Module with cell markers (from nbs directly)
- `mypackage_alt/` - Clean module (from pcts)

## Use Cases

- Different export modes for different purposes
- Intermediate formats for debugging
- Multiple package variants from same source

## Run the Example

```bash
./run_example.sh
```

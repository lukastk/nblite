# Templates Example

This example demonstrates custom notebook templates for `nbl new`.

## Templates

| Template | Description |
|----------|-------------|
| `data_analysis` | Data analysis notebook with pandas/numpy imports (default) |
| `script` | Simple script-style notebook |
| `custom_vars` | Demonstrates custom template variables |

## Configuration

```toml
[templates]
folder = "templates"
default = "data_analysis"
```

## Template Variables

Templates can use these built-in variables:
- `{{ module_name }}` - Module name (from `--name` or inferred from path)
- `{{ title }}` - Notebook title (from `--title`)
- `{{ no_export }}` - Whether to skip default_exp (from `--no-export`)
- `{{ pyproject }}` - Contents of pyproject.toml (if exists)

Custom variables can be passed via `--var key=value`.

## Run the Example

```bash
./run_example.sh
```

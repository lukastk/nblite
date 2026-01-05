# Directives Showcase

This example demonstrates all built-in nblite directives.

## Notebooks

| Notebook | Directives Covered |
|----------|-------------------|
| `01_export_basics.ipynb` | `#\|default_exp`, `#\|export`, `#\|exporti` |
| `02_export_to.ipynb` | `#\|export_to module [order]` |
| `03_export_as_func.ipynb` | `#\|export_as_func`, `#\|set_func_signature`, `#\|top_export`, `#\|func_return`, `#\|func_return_line` |
| `04_documentation.ipynb` | `#\|hide`, `#\|hide_input`, `#\|hide_output` |
| `05_evaluation.ipynb` | `#\|eval: false`, `#\|skip_evals`, `#\|skip_evals_stop` |

## Directive Summary

### Export Directives
- `#|default_exp module` - Set the default export module for a notebook
- `#|export` - Export cell to default module (included in `__all__`)
- `#|exporti` - Export cell internally (NOT in `__all__`)
- `#|export_to module [order]` - Export to specific module with optional ordering

### Function Export Directives
- `#|export_as_func` - Export notebook as a single callable function
- `#|set_func_signature` - Define the function signature and docstring
- `#|top_export` - Code placed at module level (outside the function)
- `#|func_return` - Prepend `return` to first line of cell
- `#|func_return_line` - Inline directive to mark a return line

### Documentation Directives
- `#|hide` - Hide entire cell from documentation
- `#|hide_input` - Show only output in documentation
- `#|hide_output` - Show only input in documentation

### Evaluation Directives
- `#|eval: false` - Skip cell during `nbl fill`
- `#|skip_evals` - Start skipping all following cells
- `#|skip_evals_stop` - Resume cell execution

## Run the Example

```bash
./run_example.sh
```

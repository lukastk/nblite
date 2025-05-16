# nblite

> A lightweight wrapper around [nbdev](https://github.com/AnswerDotAI/nbdev) for streamlined notebook-driven development


nblite simplifies the workflow between Jupyter notebooks, Python scripts, and module code, enhancing the notebook-driven development process.

**Note:** `nblite` is merely a wrapper around [nbdev](https://github.com/AnswerDotAI/nbdev), with some adjustments adapted to the workflow of the [Autonomy Data Unit](https://adu.autonomy.work/). Full credit of the concept and implementation of notebook-driven development using Jupyter notebooks should go to the creators of [nbdev](https://github.com/AnswerDotAI/nbdev).

<!-- #region -->
## Installation

```bash
pip install nblite
```
<!-- #endregion -->

## Core Concepts

### Code Locations
Directories containing code in different formats (notebooks, scripts, modules). Each code location is defined in the `nblite.toml` configuration file and represents a specific representation of your code:

- **Notebooks Location**: Usually contains `.ipynb` files where you write and develop your code
- **Percent Scripts Location**: Contains `.pct.py` files (notebooks converted to percent format)
- **Light Scripts Location**: Contains `.lgt.py` files (simplified percent scripts)
- **Library Location**: Contains regular Python modules exported from notebooks

### Export Pipeline
Defines the flow of code conversion between different code locations. For example, a typical pipeline might be:
```
nbs -> pts -> lib
```
This means:
1. Start with notebooks (`.ipynb`) as the source
2. Convert them to percent scripts (`.pct.py`)
3. Finally export to Python library modules (`.py`)

### Notebook Twins
Corresponding versions of the same content in different formats. When you write a notebook `my_notebook.ipynb`, nblite can create twins like:
- `my_notebook.pct.py` (percent script)
- `my_notebook.lgt.py` (light script)
- `my_module/my_notebook.py` (Python module)

These twins contain the same logical content but in different formats, allowing you to use the format that's most appropriate for the task at hand.

### Why Store Plaintext Versions?

While Jupyter notebooks (`.ipynb`) are excellent for interactive development, they pose challenges for version control systems like Git:

1. **Git-Friendly**: Plaintext formats (`.pct.py`, `.lgt.py`, `.py`) are better handled by Git, making diffs and merge conflicts easier to resolve.
2. **GitHub UI**: GitHub's interface more effectively displays changes in plaintext Python files compared to JSON-formatted notebook files.
3. **Code Review**: Reviewing code changes is more straightforward with plaintext formats.
4. **Cleaner History**: By cleaning notebook outputs before committing, you avoid polluting your Git history with large output cells and changing execution counts.
5. **Collaboration**: Team members can work with the format they prefer—notebooks for exploration, Python files for implementation.

The export pipeline ensures that changes made in one format are propagated to all twins, maintaining consistency across representations.

<!-- #region -->
## Key Features

- **Export Pipeline**: Convert notebooks between different formats (.ipynb, percent scripts, light scripts, and Python modules)
- **Documentation**: Generate documentation from notebooks using Quarto
- **Git Integration**: Clean notebooks and enforce consistent git commits
- **Parallel Execution**: Execute notebooks in parallel for faster workflow
- **Export as Functions**: Notebooks can be exported as functions

## Quick Start

### Initialize a project

```bash
# Create a new nblite project
nbl init --module-name my_project
```

### Create a new notebook

```bash
# Create a new notebook in a code location
nbl new nbs/my_notebook.ipynb
```

### Fill Notebooks with Outputs

The `nbl fill` command is used to execute all the cells in all `.ipynb` notebooks.
 
```bash
nbl fill
```

This command also works as a testing command.

### Prepare your project

```bash
# Export, clean, and fill notebooks in one command
nbl prepare
```

## Configuration

nblite uses a TOML configuration file (`nblite.toml`) at the project root:

```toml
export_pipeline = """
nbs -> pts
pts -> lib
"""
docs_cl = "nbs"
docs_title = "My Project"

[cl.lib]
path = "my_module"
format = "module"

[cl.nbs]
format = "ipynb"

[cl.pts]
format = "percent"
```
<!-- #endregion -->

## Common Commands

Run `nbl` to see all available commands.

### Export and Conversion

- `nbl export`: Export notebooks according to the export pipeline
- `nbl convert <nb_path> <dest_path>`: Convert a notebook between formats
- `nbl clear`: Clear downstream code locations

### Notebook Management

- `nbl clean`: Clean notebooks by removing outputs and metadata
- `nbl fill`: Execute notebooks and fill with outputs
- `nbl test`: Test that notebooks execute without errors (dry run of fill)

### Documentation

- `nbl readme`: Generate README.md from index.ipynb
- `nbl render-docs`: Render project documentation using Quarto
- `nbl preview-docs`: Preview documentation 

### Git Integration

- `nbl git-add`: Add files to git staging with proper cleaning
- `nbl validate-staging`: Validate that staged notebooks are clean
- `nbl install-hooks`: Install git hooks for the project

## Development Workflow

1. Write code in Jupyter notebooks (.ipynb)
2. Run `nbl export` to convert to other formats
3. Run `nbl clean` before committing to git
4. Use `nbl fill` (or `nbl test` if outputs are not to be rendered) to verify your notebooks execute correctly
5. Use `nbl render-docs` to generate documentation, or use `nbl preview-docs` to preview the documentation.

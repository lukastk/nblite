# nblite

> A lightweight wrapper around [nbdev](https://github.com/AnswerDotAI/nbdev) for streamlined notebook-driven development


nblite simplifies the workflow between Jupyter notebooks, Python scripts, and module code, enhancing the notebook-driven development process.

**Note:** `nblite` is merely a wrapper around [nbdev](https://github.com/AnswerDotAI/nbdev) with some adjustments and additions adapted to the needs of the [Autonomy Data Unit](https://adu.autonomy.work/). Full credit of the concept and implementation of notebook-driven development using Jupyter notebooks should go to the creators of [nbdev](https://github.com/AnswerDotAI/nbdev).

<!-- #region -->
## Installation

```bash
pip install nblite
```
<!-- #endregion -->

<!-- #region -->
## Core Concepts

### Code locations
Directories containing code in different formats (notebooks, scripts, modules). Each code location is defined in the `nblite.toml` configuration file and will store different representations of your code. Available formats are:

<table>
    <thead>
        <tr>
            <th>Format</th>
            <th>Format key</th>
            <th>File Extension</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Python module</td>
            <td><code>module</code></code></td>
            <td><code>py</code></td>
        </tr>
        <tr>
            <td>Jupyter notebook</td>
            <td><code>ipynb</code></td>
            <td><code>ipynb</code></td>
        </tr>
        <tr>
            <td><a href="https://github.com/mwouts/jupytext/blob/main/demo/World%20population.pct.py">Percent</a></td>
            <td><code>percent</code></td>
            <td><code>pct.py</code></td>
        </tr>
        <tr>
            <td><a href="https://github.com/mwouts/jupytext/blob/main/demo/World%20population.lgt.py">Light</a></td>
            <td><code>light</code></td>
            <td><code>lgt.py</code></td>
        </tr>
        <tr>
            <td>
                <a href="https://github.com/mwouts/jupytext/blob/main/demo/World%20population.spx.py">Sphinx</a>
            </td>
            <td><code>sphinx</code></td>
            <td><code>spx.py</code></td>
        </tr>
        <tr>
            <td><a href="https://github.com/mwouts/jupytext/blob/main/demo/World%20population.myst.md">Myst</a></td>
            <td><code>myst</code></td>
            <td><code>myst.md</code></td>
        </tr>
        <tr>
            <td><a href="https://github.com/mwouts/jupytext/blob/main/demo/World%20population.pandoc.md">Pandoc</a></td>
            <td><code>pandoc</code></td>
            <td><code>pandoc.md</code></td>
    </tr>
    </tbody>
</table>


In the `nblite.toml` you define the code locations and the formats of the code within them:

```toml
[cl.nbs]
format="ipynb"
path="notebooks"

[cl.pts]
format="percent"
path="percent_notebooks"

[cl.lib]
format="module"
path="nblite"
```

Here we have defined three code locations (`nbs`, `pts` and `lib`) and specified their paths (relative to the project root) and their formats. Read more about plaintext notebook formats [here](https://jupytext.readthedocs.io/en/latest/formats-scripts.html#the-percent-format).
<!-- #endregion -->


### Export pipeline
Defines the flow of code conversion between different code locations. For example, a typical pipeline might be:
```
nbs -> pts
pts -> lib
```
This means:
1. Start with notebooks (`.ipynb`) as the source
2. Convert them to percent scripts (`.pct.py`)
3. Finally export to Python library modules (`.py`)

### Notebook 'twins'

Corresponding versions of the same content in different formats. When you write a notebook `my_notebook.ipynb`, nblite can create twins like:
- `my_notebook.pct.py` (percent script)
- `my_notebook.lgt.py` (light script)
- `my_module/my_notebook.py` (Python module)

These twins contain the same logical content but in different formats, allowing you to use the format that's most appropriate for the task at hand.

### Why store plaintext versions?

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

### Set up Git hooks

```bash
# Install pre-commit hooks for automatic notebook cleaning
nbl install-hooks
```

Git hooks ensure that notebooks are properly cleaned before committing. The pre-commit hook automatically:
- Validates that notebooks are clean (removes metadata and outputs)
- Ensures that all notebook twins are consistent
- Prevents accidental commits of unclean notebooks

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

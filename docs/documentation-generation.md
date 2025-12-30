# Documentation Generation

nblite can generate documentation websites from your notebooks using popular static site generators. This guide covers setup, configuration, and best practices.

## Overview

nblite supports three documentation generators:

| Generator | Installation | Best For |
|-----------|-------------|----------|
| **MkDocs** | `pip install mkdocs mkdocs-material mkdocs-jupyter` | Simple, fast documentation |
| **Jupyter Book** | `pip install jupyter-book` | Book-style documentation with execution |
| **Quarto** | [Download](https://quarto.org/) | Scientific publishing |

## Quick Start

### 1. Configure Documentation

Add to `nblite.toml`:

```toml
docs_cl = "nbs"           # Code location with notebooks
docs_title = "My Project" # Documentation title
docs_generator = "mkdocs" # Generator to use
```

### 2. Build Documentation

```bash
nbl render-docs
```

This creates documentation in `_docs/` (by default).

### 3. Preview Documentation

```bash
nbl preview-docs
```

Opens a local server with live reload.

## Configuration

### Basic Options

```toml
# Top-level shortcuts
docs_cl = "nbs"
docs_title = "My Project Documentation"
docs_generator = "mkdocs"
```

### Full Options

```toml
[docs]
# Code location to document
code_location = "nbs"

# Documentation title
title = "My Project Documentation"

# Author name
author = "Your Name"

# Output folder
output_folder = "_docs"

# Execute notebooks during build
execute_notebooks = false

# Patterns to exclude
exclude_patterns = ["__*", ".*", "**/internal/*"]
```

## MkDocs

MkDocs is the default generator, offering fast builds and a clean interface.

### Installation

```bash
pip install mkdocs mkdocs-material mkdocs-jupyter
```

### Features

- Fast build times
- Beautiful Material theme
- Full-text search
- Mobile-friendly

### Building

```bash
nbl render-docs -g mkdocs
```

### Previewing

```bash
nbl preview-docs -g mkdocs
```

Starts a server at `http://localhost:8000` with live reload.

### Customization

Create `mkdocs.yml` in your project for advanced customization:

```yaml
site_name: My Project
theme:
  name: material
  palette:
    primary: blue
nav:
  - Home: index.md
  - Tutorial: tutorial.md
  - API: api.md
```

## Jupyter Book

Jupyter Book creates book-style documentation with interactive features.

### Installation

```bash
pip install jupyter-book
```

### Features

- Book-style navigation
- Interactive widgets
- Executable notebooks
- Citations and references

### Building

```bash
nbl render-docs -g jupyterbook
```

### Previewing

```bash
nbl preview-docs -g jupyterbook
```

### Customization

Create `_config.yml` for Jupyter Book configuration:

```yaml
title: My Project
author: Your Name
execute:
  execute_notebooks: "off"
sphinx:
  config:
    html_theme: sphinx_book_theme
```

## Quarto

Quarto is a powerful publishing system for technical content.

### Installation

Download from [quarto.org](https://quarto.org/).

### Features

- Multiple output formats (HTML, PDF, Word)
- Scientific publishing features
- Cross-references
- Advanced layouts

### Building

```bash
nbl render-docs -g quarto
```

### Previewing

```bash
nbl preview-docs -g quarto
```

### Customization

Create `_quarto.yml` for Quarto configuration:

```yaml
project:
  type: website

website:
  title: "My Project"
  navbar:
    left:
      - href: index.qmd
        text: Home

format:
  html:
    theme: cosmo
```

## Documentation Directives

Control how cells appear in documentation:

### Hide Entire Cell

```python
#|hide
# This cell is completely hidden
import internal_module
setup()
```

### Hide Input Only

```python
#|hide_input
# Code hidden, output shown
plt.plot(data)
plt.show()
```

### Hide Output Only

```python
#|hide_output
# Code shown, output hidden
model.fit(X, y, verbose=True)
```

## Organizing Documentation

### File Structure

Organize notebooks for clear documentation:

```
nbs/
├── 00_index.ipynb      # Home page
├── 01_getting_started.ipynb
├── 02_tutorial.ipynb
├── 03_api_reference.ipynb
└── 04_examples.ipynb
```

Notebooks are sorted alphabetically, so use numeric prefixes for ordering.

### Navigation

For MkDocs, create a custom navigation in `mkdocs.yml`:

```yaml
nav:
  - Home: 00_index.md
  - Getting Started: 01_getting_started.md
  - Tutorial:
    - Basics: 02a_basics.md
    - Advanced: 02b_advanced.md
  - API Reference: 03_api_reference.md
```

### Multiple Sections

Use subdirectories for complex documentation:

```
nbs/
├── index.ipynb
├── tutorial/
│   ├── 01_basics.ipynb
│   └── 02_advanced.ipynb
├── api/
│   ├── core.ipynb
│   └── utils.ipynb
└── examples/
    ├── example1.ipynb
    └── example2.ipynb
```

## Best Practices

### 1. Write for Readers

Notebooks in documentation should be readable:

```python
# Bad
df=pd.read_csv('data.csv');df.head()

# Good
# Load the sample dataset
df = pd.read_csv('data.csv')

# Preview the first few rows
df.head()
```

### 2. Use Markdown Cells Liberally

Explain what code does:

**Markdown cell:**
```markdown
## Data Loading

First, we load the dataset from CSV. The dataset contains
1000 samples with 10 features each.
```

**Code cell:**
```python
df = pd.read_csv('data.csv')
print(f"Loaded {len(df)} samples with {len(df.columns)} features")
```

### 3. Hide Setup Code

```python
#|hide
# Boring setup that readers don't need to see
import warnings
warnings.filterwarnings('ignore')
plt.style.use('seaborn')
```

### 4. Show Outputs Selectively

```python
#|hide_input
# Let the visualization speak for itself
create_beautiful_chart(data)
```

### 5. Test Documentation

```bash
# Verify notebooks execute
nbl test

# Build documentation
nbl render-docs

# Check for broken links, etc.
```

## README Generation

Generate README.md from a notebook:

### Configuration

```toml
readme_nb_path = "nbs/index.ipynb"
```

### Generate

```bash
nbl readme
```

Or specify the notebook:

```bash
nbl readme nbs/getting_started.ipynb -o README.md
```

### Best Practices for README

Your README notebook should include:
- Project title and description
- Installation instructions
- Quick start example
- Links to full documentation

Use `#|hide` for cells that shouldn't appear in README.

## Deployment

### GitHub Pages

**Using GitHub Actions:**

```yaml
# .github/workflows/docs.yml
name: Deploy Docs

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install nblite
          pip install mkdocs mkdocs-material mkdocs-jupyter

      - name: Build docs
        run: nbl render-docs

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./_docs
```

### Read the Docs

Create `.readthedocs.yml`:

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

python:
  install:
    - method: pip
      path: .
    - requirements: docs/requirements.txt

mkdocs:
  configuration: mkdocs.yml
```

### Netlify

Create `netlify.toml`:

```toml
[build]
  command = "pip install nblite && nbl render-docs"
  publish = "_docs"

[build.environment]
  PYTHON_VERSION = "3.11"
```

## Troubleshooting

### "Generator not found"

Install the required generator:

```bash
# MkDocs
pip install mkdocs mkdocs-material mkdocs-jupyter

# Jupyter Book
pip install jupyter-book

# Quarto - download from website
```

### "No docs_cl configured"

Add to `nblite.toml`:

```toml
docs_cl = "nbs"
```

Or specify on command line:

```bash
nbl render-docs --docs-cl nbs
```

### Notebooks Not Appearing

Check:
1. Notebooks are in the configured `docs_cl` location
2. Notebooks aren't matching `exclude_patterns`
3. Notebooks don't start with `__` or `.`

### Build Errors

1. Check notebooks execute without errors:
   ```bash
   nbl test
   ```

2. Check for syntax errors in configuration files

3. Try building with verbose output:
   ```bash
   nbl render-docs 2>&1 | tee build.log
   ```

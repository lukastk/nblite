# nblite

Notebook-driven Python package development tool.

A modern alternative to nbdev that enables developers to write Python packages entirely in Jupyter notebooks, with automatic export to Python modules, synchronization between formats, and integrated documentation generation.

## Installation

```bash
pip install nblite
```

## Quick Start

```bash
# Initialize a new nblite project
nbl init

# Create a new notebook
nbl new nbs/utils.ipynb -n utils

# Export notebooks to Python modules
nbl export

# Build documentation
nbl docs build
```

## Features

- **Notebook → Module Export**: Convert Jupyter notebooks to Python packages using directives like `#|export`
- **Format Synchronization**: Keep notebooks (ipynb), plaintext scripts (pct.py), and modules (.py) in sync
- **Git Integration**: Pre-commit hooks for cleaning notebooks and validating staging
- **Documentation**: Generate documentation sites from notebooks using Jupyter Book or MkDocs

## License

MIT

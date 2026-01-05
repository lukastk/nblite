#!/bin/bash
# From Module Example
# Demonstrates converting Python modules to notebooks

set -e
cd "$(dirname "$0")"

echo "=== From Module Example ==="
echo ""

# Clean up any existing notebooks and exports
rm -rf nbs/*
nbl clear --all 2>/dev/null || true

echo "Source Python files in src/:"
ls -1 src/*.py
echo ""

echo "Converting single file (src/utils.py -> nbs/utils.ipynb):"
nbl from-module src/utils.py nbs/utils.ipynb
echo ""

echo "Converting directory (src/ -> nbs/):"
nbl from-module src/ nbs/ --recursive
echo ""

echo "Generated notebooks:"
ls -1 nbs/
echo ""

echo "Content of nbs/utils.ipynb (converted from src/utils.py):"
echo "=========================================================="
# Show the first few cells
python -c "
import json
with open('nbs/utils.ipynb') as f:
    nb = json.load(f)
for cell in nb['cells'][:3]:
    print(f'--- {cell[\"cell_type\"]} ---')
    src = cell.get('source', '')
    if isinstance(src, list):
        src = ''.join(src)
    # Show first 500 chars
    print(src[:500])
    if len(src) > 500:
        print('...')
    print()
"

echo ""
echo "=== Running fill and export ==="
echo ""

# Fill notebooks (execute and save outputs, auto-cleans)
echo "Filling notebooks..."
nbl fill
echo ""

# Run export
echo "Running export..."
nbl export

echo ""
echo "=== Exported module ==="
ls -1 mypackage/*.py 2>/dev/null | grep -v __init__ || echo "  (no modules exported)"

echo ""
echo "=== Example complete ==="

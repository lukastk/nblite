#!/bin/bash
# Fill Execution Example
# Demonstrates notebook execution configuration

set -e
cd "$(dirname "$0")"

echo "=== Fill Execution Example ==="
echo ""

echo "Fill configuration from nblite.toml:"
grep -A 10 "^\[fill\]" nblite.toml
echo ""

echo "Notebooks to execute:"
ls -1 nbs/*.ipynb
echo ""

echo "Running nbl test (dry-run, checks for errors)..."
nbl test || echo "(Note: test may show warnings)"
echo ""

echo "Running nbl fill (execute and save outputs)..."
nbl fill
echo ""

echo "Checking outputs were saved:"
python -c "
import json
for nb_name in ['runnable.ipynb', 'quick_test.ipynb']:
    with open(f'nbs/{nb_name}') as f:
        nb = json.load(f)
    code_cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
    cells_with_output = sum(1 for c in code_cells if c.get('outputs'))
    print(f'{nb_name}: {cells_with_output}/{len(code_cells)} cells have outputs')
"

echo ""
echo "Running export (no pipeline configured, so this is a no-op)..."
nbl export

echo ""
echo "=== Example complete ==="

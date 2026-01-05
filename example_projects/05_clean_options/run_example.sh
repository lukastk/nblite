#!/bin/bash
# Clean Options Example
# Demonstrates various notebook cleaning configurations

set -e
cd "$(dirname "$0")"

echo "=== Clean Options Example ==="
echo ""

echo "Before cleaning - notebook has outputs and execution counts:"
echo "============================================================"
python -c "
import json
with open('nbs/example.ipynb') as f:
    nb = json.load(f)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        exec_count = cell.get('execution_count', 'None')
        output_count = len(cell.get('outputs', []))
        print(f'Cell {i}: execution_count={exec_count}, outputs={output_count}')
"

echo ""
echo "Running nbl fill (with auto-clean based on config)..."
nbl fill

echo ""
echo "After fill (auto-cleaned):"
echo "==============="
python -c "
import json
with open('nbs/example.ipynb') as f:
    nb = json.load(f)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        exec_count = cell.get('execution_count', 'None')
        output_count = len(cell.get('outputs', []))
        print(f'Cell {i}: execution_count={exec_count}, outputs={output_count}')
"

echo ""
echo "Clean configuration from nblite.toml:"
grep -A 15 "^\[clean\]" nblite.toml

echo ""
echo "Running export (no pipeline configured, so this is a no-op)..."
nbl export

echo ""
echo "=== Example complete ==="

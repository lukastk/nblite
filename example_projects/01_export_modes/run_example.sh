#!/bin/bash
# Export Modes Example
# Demonstrates the difference between 'percent' and 'py' export modes

set -e
cd "$(dirname "$0")"

echo "=== Export Modes Example ==="
echo ""

# Fill notebooks (execute and save outputs, auto-cleans)
echo "Filling notebooks..."
nbl fill
echo ""

# Clear any existing exports
echo "Clearing existing exports..."
nbl clear --all 2>/dev/null || true

# Run export
echo "Running export..."
nbl export

echo ""
echo "=== Comparing export modes ==="
echo ""

echo "--- mypackage_percent/utils.py (export_mode = 'percent') ---"
echo "Notice the cell markers (# %% ...) that reference the source notebook:"
echo ""
cat mypackage_percent/utils.py

echo ""
echo ""
echo "--- mypackage_plain/utils.py (export_mode = 'py') ---"
echo "Clean Python without any cell markers:"
echo ""
cat mypackage_plain/utils.py

echo ""
echo "=== Example complete ==="

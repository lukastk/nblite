#!/bin/bash
# Extensions Example
# Demonstrates the nblite hook/extension system

set -e
cd "$(dirname "$0")"

echo "=== Extensions Example ==="
echo ""

echo "Extension file (nblite_ext.py) contents:"
echo "----------------------------------------"
head -30 nblite_ext.py
echo "..."
echo ""

# Fill notebooks (execute and save outputs, auto-cleans)
echo "Filling notebooks..."
nbl fill
echo ""

# Clear any existing exports
echo "Clearing existing exports..."
nbl clear --all 2>/dev/null || true
echo ""

echo "Running export (watch for [EXT] messages from extension):"
echo "=========================================================="
nbl export

echo ""
echo "=== Example complete ==="

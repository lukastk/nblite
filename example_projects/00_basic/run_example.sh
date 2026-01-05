#!/bin/bash
# Basic Example
# Demonstrates basic three-stage pipeline: nbs -> pcts -> lib

set -e
cd "$(dirname "$0")"

echo "=== Basic Example ==="
echo ""

echo "Pipeline configuration:"
grep -A 5 "export_pipeline" nblite.toml
echo ""

# Fill notebooks (execute and save outputs, auto-cleans)
echo "Filling notebooks..."
nbl fill
echo ""

# Clear existing exports
echo "Clearing existing exports..."
nbl clear --all 2>/dev/null || true
echo ""

# Run export
echo "Running export..."
nbl export

echo ""
echo "=== Generated Files ==="
echo ""

echo "pcts/ (percent format):"
ls -1 pcts/*.pct.py 2>/dev/null || echo "  (empty)"
echo ""

echo "my_lib/ (module format):"
ls -1 my_lib/*.py | grep -v __init__ 2>/dev/null || echo "  (empty)"

echo ""
echo "=== Example complete ==="

#!/bin/bash
# Multi-Pipeline Example
# Demonstrates complex multi-branch export pipelines

set -e
cd "$(dirname "$0")"

echo "=== Multi-Pipeline Example ==="
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

echo "mypackage/ (export_mode = percent):"
ls -1 mypackage/*.py | grep -v __init__ 2>/dev/null || echo "  (empty)"
echo ""

echo "mypackage_alt/ (export_mode = py):"
ls -1 mypackage_alt/*.py | grep -v __init__ 2>/dev/null || echo "  (empty)"
echo ""

echo "=== Comparing Export Modes ==="
echo ""

echo "--- mypackage/core.py (with cell markers) ---"
head -15 mypackage/core.py
echo "..."
echo ""

echo "--- mypackage_alt/core.py (clean Python) ---"
head -15 mypackage_alt/core.py
echo "..."

echo ""
echo "=== Example complete ==="

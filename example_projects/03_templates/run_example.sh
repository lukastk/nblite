#!/bin/bash
# Templates Example
# Demonstrates custom notebook templates with nbl new

set -e
cd "$(dirname "$0")"

echo "=== Templates Example ==="
echo ""

# Clean up any existing notebooks
rm -f nbs/*.ipynb nbs/*.pct.py

echo "Available templates in templates/:"
ls -1 templates/
echo ""

echo "=== Creating notebooks with different templates ==="
echo ""

echo "1. Using default template (data_analysis):"
nbl new nbs/analysis.ipynb --name my_analysis --title "My Analysis"
echo "   Created nbs/analysis.ipynb"
echo ""

echo "2. Using script template:"
nbl new nbs/my_script.ipynb --template script --name my_script
echo "   Created nbs/my_script.ipynb"
echo ""

echo "3. Using custom_vars template with --var options:"
nbl new nbs/versioned.ipynb --template custom_vars --name versioned \
    --var author="Jane Doe" \
    --var version="1.2.3" \
    --var description="A versioned module"
echo "   Created nbs/versioned.ipynb"
echo ""

echo "4. Creating without export directive (--no-export):"
nbl new nbs/scratch.ipynb --no-export --title "Scratch Pad"
echo "   Created nbs/scratch.ipynb"
echo ""

echo "=== Generated Notebooks ==="
echo ""
ls -1 nbs/

echo ""
echo "=== Content of nbs/versioned.ipynb (showing custom variables) ==="
echo ""
# Convert to percent format and display (easier to read)
nbl convert nbs/versioned.ipynb --format percent --stdout 2>/dev/null || cat nbs/versioned.ipynb

echo ""
echo "=== Running fill and export ==="
echo ""

# Fill notebooks (execute and save outputs, auto-cleans)
echo "Filling notebooks..."
nbl fill
echo ""

# Clear any existing exports
echo "Clearing existing exports..."
nbl clear --all 2>/dev/null || true
echo ""

# Run export
echo "Running export..."
nbl export

echo ""
echo "=== Example complete ==="

#!/bin/bash
# Directives Showcase Example
# Demonstrates all built-in nblite directives

set -e
cd "$(dirname "$0")"

echo "=== Directives Showcase Example ==="
echo ""

# Clear any existing exports
echo "Clearing existing exports..."
nbl clear --all 2>/dev/null || true

# Run export
echo "Running export..."
nbl export

echo ""
echo "=== Exported Modules ==="
echo ""
ls -1 mypackage/*.py | grep -v __init__

echo ""
echo "=== Sample Output: export_basics.py ==="
echo "Notice #|export adds to __all__, #|exporti does not:"
echo ""
cat mypackage/export_basics.py

echo ""
echo "=== Sample Output: data_processor.py ==="
echo "Shows #|export_as_func - notebook exported as a function:"
echo ""
cat mypackage/data_processor.py

echo ""
echo "=== Example complete ==="

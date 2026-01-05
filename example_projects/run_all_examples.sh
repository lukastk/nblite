#!/bin/bash
# Run All Examples
# Loops through all example projects and runs their run_example.sh scripts

set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "  Running All nblite Example Projects"
echo "=========================================="
echo ""

# Find all example directories with run_example.sh
failed=0
passed=0

for example_dir in */; do
    # Skip if no run_example.sh
    if [ ! -f "${example_dir}run_example.sh" ]; then
        continue
    fi

    example_name="${example_dir%/}"
    echo ""
    echo "=========================================="
    echo "  Running: $example_name"
    echo "=========================================="
    echo ""

    if (cd "$example_dir" && ./run_example.sh); then
        echo ""
        echo "[PASS] $example_name completed successfully"
        ((passed++))
    else
        echo ""
        echo "[FAIL] $example_name failed!"
        ((failed++))
    fi
done

echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo "Passed: $passed"
echo "Failed: $failed"
echo ""

if [ $failed -gt 0 ]; then
    echo "Some examples failed!"
    exit 1
else
    echo "All examples passed!"
    exit 0
fi

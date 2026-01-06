#!/bin/bash
# Run All Examples
# Loops through all example projects and runs their run_example.sh scripts in parallel

cd "$(dirname "$0")"

echo "=========================================="
echo "  Running All nblite Example Projects"
echo "=========================================="
echo ""

# Create temp directory for output files
tmp_dir=$(mktemp -d)
trap "rm -rf $tmp_dir" EXIT

# Find all example directories with run_example.sh
declare -a example_names
declare -a pids

for example_dir in */; do
    # Skip if no run_example.sh
    if [ ! -f "${example_dir}run_example.sh" ]; then
        continue
    fi

    example_name="${example_dir%/}"
    example_names+=("$example_name")

    echo "Starting: $example_name"

    # Run in background, capture stdout and stderr separately
    (
        cd "$example_dir" && ./run_example.sh \
            > "$tmp_dir/${example_name}.stdout" \
            2> "$tmp_dir/${example_name}.stderr"
        echo $? > "$tmp_dir/${example_name}.exitcode"
    ) &
    pids+=($!)
done

echo ""
echo "Waiting for all examples to complete..."
echo ""

# Wait for all background jobs
for pid in "${pids[@]}"; do
    wait "$pid"
done

# Collect results
failed=0
passed=0
failed_examples=()

for example_name in "${example_names[@]}"; do
    exitcode=$(cat "$tmp_dir/${example_name}.exitcode" 2>/dev/null || echo "1")

    if [ "$exitcode" -eq 0 ]; then
        echo "[PASS] $example_name"
        ((passed++))
    else
        echo "[FAIL] $example_name"
        ((failed++))
        failed_examples+=("$example_name")
    fi
done

echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo "Passed: $passed"
echo "Failed: $failed"

if [ $failed -gt 0 ]; then
    echo ""
    echo "Failed examples:"
    for example in "${failed_examples[@]}"; do
        echo "  - $example"
    done

    echo ""
    echo "=========================================="
    echo "  Error Output (stderr)"
    echo "=========================================="

    for example in "${failed_examples[@]}"; do
        stderr_file="$tmp_dir/${example}.stderr"
        if [ -s "$stderr_file" ]; then
            echo ""
            echo "--- $example stderr ---"
            cat "$stderr_file"
        fi

        # Also show stdout if stderr is empty (errors might be in stdout)
        stdout_file="$tmp_dir/${example}.stdout"
        if [ ! -s "$stderr_file" ] && [ -s "$stdout_file" ]; then
            echo ""
            echo "--- $example stdout (stderr was empty) ---"
            tail -50 "$stdout_file"
        fi
    done

    echo ""
    exit 1
else
    echo ""
    echo "All examples passed!"
    exit 0
fi

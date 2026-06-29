#!/usr/bin/env bash
# eval-viewer.sh — Generate and open an HTML eval report for okf-schema
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the latest iteration directory
LATEST_ITERATION=$(find "$SCRIPT_DIR" -maxdepth 1 -type d -name 'iteration-*' | sort -V | tail -n 1)

if [ -z "$LATEST_ITERATION" ]; then
    echo "❌ No iteration directories found. Run the eval campaign first."
    echo "   Expected: skills-evals/iteration-1/"
    exit 1
fi

ITERATION_NAME=$(basename "$LATEST_ITERATION")
OUTPUT_FILE="$SCRIPT_DIR/eval-report.html"

echo "=== OKF Schema Eval Viewer ==="
echo "Iteration: $ITERATION_NAME"
echo "Output:    $OUTPUT_FILE"
echo ""

# Generate the report
python3 "$SCRIPT_DIR/eval-viewer.py" \
    --iteration "$LATEST_ITERATION" \
    --output "$OUTPUT_FILE"

echo ""
echo "✅ Report generated: $OUTPUT_FILE"

# Open in browser (macOS)
if command -v open >/dev/null 2>&1; then
    open "$OUTPUT_FILE"
    echo "🌐 Opened in browser"
fi

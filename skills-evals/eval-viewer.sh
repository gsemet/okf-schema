#!/usr/bin/env bash
# eval-viewer.sh — Generate and open an HTML eval report for okf-schema
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the latest iteration directory under results/
RESULTS_DIR="$SCRIPT_DIR/results"
LATEST_ITERATION=$(find "$RESULTS_DIR" -maxdepth 1 -type d -name 'iteration-*' | sort -V | tail -n 1)

if [ -z "$LATEST_ITERATION" ]; then
    echo "❌ No iteration directories found. Run the eval campaign first."
    echo "   Expected: skills-evals/results/iteration-DD.MM.YY-HH.MM/"
    exit 1
fi

ITERATION_NAME=$(basename "$LATEST_ITERATION")
OUTPUT_FILE="$LATEST_ITERATION/eval-result.html"

echo "=== OKF Schema Eval Viewer ==="
echo "Iteration: $ITERATION_NAME"
echo "Output:    $OUTPUT_FILE"
echo ""

# Generate the report (output defaults to iteration dir)
python3 "$SCRIPT_DIR/eval-viewer.py" \
    --iteration "$LATEST_ITERATION"

echo ""
echo "✅ Report generated: $OUTPUT_FILE"

# Open in browser (macOS)
if command -v open >/dev/null 2>&1; then
    open "$OUTPUT_FILE"
    echo "🌐 Opened in browser"
fi

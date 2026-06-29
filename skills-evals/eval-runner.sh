#!/usr/bin/env bash
# eval-runner.sh — Pre-flight checks and scoring for OKF skill evaluation campaign
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EVAL_DIR="$PROJECT_DIR/skills-evals"
RESULTS_DIR="$EVAL_DIR/results"

mkdir -p "$RESULTS_DIR"

echo "=== OKF Schema Skill Eval Runner ==="
echo "Project dir: $PROJECT_DIR"
echo "Results dir: $RESULTS_DIR"
echo ""

# Verify dependencies
echo "Checking okf-schema..."
if ! uv run -- okf-schema --version >/dev/null 2>&1; then
    echo "ERROR: okf-schema not found. Run 'uv sync' to install dependencies."
    exit 1
fi

# Verify fixtures
echo "Checking fixtures..."
for fixture in conformant-bundle non-conformant schema-valid-bundle schema-invalid-bundle schema-db schema-db-yaml; do
    if [ ! -d "$EVAL_DIR/fixtures/$fixture" ]; then
        echo "ERROR: Missing fixture: $fixture"
        exit 1
    fi
done

echo "All checks passed."
echo ""

# Check for iteration directories
LATEST_ITERATION=$(find "$EVAL_DIR" -maxdepth 1 -type d -name 'iteration-*' | sort -V | tail -n 1)

if [ -n "$LATEST_ITERATION" ]; then
    ITERATION_NAME=$(basename "$LATEST_ITERATION")
    echo "Found iteration: $ITERATION_NAME"
    echo "  Location: $LATEST_ITERATION"
    echo ""
    echo "Eval cases found:"
    for eval_dir in "$LATEST_ITERATION"/*/; do
        if [ -d "$eval_dir" ]; then
            name=$(basename "$eval_dir")
            has_with_skill=$([ -d "$eval_dir/with_skill" ] && echo "✅" || echo "❌")
            has_without_skill=$([ -d "$eval_dir/without_skill" ] && echo "✅" || echo "❌")
            echo "  - $name  with_skill:$has_with_skill  without_skill:$has_without_skill"
        fi
    done
    echo ""
    echo "To view the report, run: just eval-view-okf-schema"
else
    echo "No iteration directories found yet."
    echo ""
    echo "To trigger the eval campaign:"
    echo "  1. Run: just copilot-cli-eval-okf-schema"
    echo "  2. Or open this prompt in Copilot: skills-evals/eval.prompt.md"
fi

uv := "uv"
uv_run := uv + " run --no-sync --"
PACKAGE_NAME := "okf_schema"

# Show this help message
help:
    @just --list

# Install all dependencies (including dev)
dev:
    {{ uv }} sync --all-groups

update:
    rm -rf uv.lock
    {{ uv }} sync

# Run the full preflight check: style-check, lint, typecheck, test, refresh-examples
preflight:
    just style-check
    just lint
    just changelog
    just typecheck
    just test
    just refresh-examples

# Run tests with coverage
[group("test")]
test:
    {{ uv_run }} pytest

# Run tests in parallel with xdist
[group("test")]
test-fast:
    {{ uv_run }} pytest -n auto

# Format code with ruff
[group("format")]
style:
    {{ uv_run }} ruff format src tests
    {{ uv_run }} ruff check --fix src tests

# Check formatting without modifying files
[group("format")]
style-check:
    {{ uv_run }} ruff format --check src tests
    {{ uv_run }} ruff check src tests

# Run linters (ruff)
[group("lint")]
lint:
    {{ uv_run }} ruff check src tests

# Run type checkers (ty + mypy)
[group("typecheck")]
typecheck:
    {{ uv_run }} ty check src
    {{ uv_run }} mypy src

# Build Sphinx documentation (regenerates CHANGELOG first)
[group("docs")]
docs:
    just changelog
    {{ uv_run }} sphinx-build -b html docs/source docs/_build/html

# Serve documentation locally
[group("docs")]
docs-serve: docs
    {{ uv_run }} python -m http.server 8000 --directory docs/_build/html

# Open documentation locally
[group("docs")]
[macos]
docs-open:
    open docs/_build/html/index.html

# Open documentation locally
[group("docs")]
[linux]
docs-open:
    xdg-open docs/_build/html/index.html


# Clean build artifacts
[group("clean")]
clean:
    find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find . -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
    find . -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
    find . -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
    find . -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null || true
    rm -rf build dist docs/_build htmlcov .coverage coverage.xml 2>/dev/null || true

# Regenerate CHANGELOG.md from conventional commits
[group("build")]
changelog:
    {{ uv_run }} cz changelog

# Build package distributions
[group("build")]
build:
    {{ uv }} build

[group("build")]
refresh-examples:
    {{ uv_run }} okf-schema index --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema lint --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema validate --path examples/ai-llm-knowledge-base --strict
    {{ uv_run }} okf-schema stats --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema list --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema backlinks --path examples/ai-llm-knowledge-base papers/attention-is-all-you-need papers/toolformer
    rm -rf examples/specific-hw-knowledge-base/
    {{ uv_run }} okfkb init examples/specific-hw-knowledge-base/
    {{ uv_run }} okfkb new-finding examples/specific-hw-knowledge-base/ --title "HW Failure investigation" --confidence low --context "Hardware failure pattern observed in production logs during stress testing."
    {{ uv_run }} okf-schema index --path examples/specific-hw-knowledge-base/
    {{ uv_run }} okf-schema lint --path examples/specific-hw-knowledge-base/
    {{ uv_run }} okf-schema validate --strict --path examples/specific-hw-knowledge-base/


# ── Skill Evals ──────────────────────────────────────────────────────────────

# Trigger okf-schema skill eval via Copilot-CLI
[group('eval')]
copilot-cli-eval-okf-schema:
    # Or in Copilot chat: "Please follow the instructions in skills-evals/eval.prompt.md"
    copilot --prompt skills-evals/eval.prompt.md

# Score okf-schema eval outputs and generate report
[group('eval')]
eval-okf-schema:
    bash skills-evals/eval-runner.sh
    bash skills-evals/eval-viewer.sh

# Grade all evals in the specified iteration using deterministic automated grader
[group('eval')]
eval-grade-okf-schema iteration="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{ iteration }}" ]; then
        LATEST=$(find skills-evals/results -maxdepth 1 -type d -name 'iteration-*' | sort -V | tail -n 1)
        if [ -z "$LATEST" ]; then
            echo "❌ No iteration directories found in skills-evals/results/"
            exit 1
        fi
        echo "Using latest iteration: $(basename "$LATEST")"
        uv run -- python skills-evals/grade-eval.py --iteration "$LATEST"
    else
        uv run -- python skills-evals/grade-eval.py --iteration skills-evals/results/{{ iteration }}
    fi

# Open okf-schema eval review in browser
[group('eval')]
eval-view-okf-schema:
    bash skills-evals/eval-viewer.sh

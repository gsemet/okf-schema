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

update-guidelines:
    guidelines update

# Run the full preflight check: style-check, lint, typecheck, test, docs
preflight:
    if [ -n "${CI:-}" ]; then \
        just style-check; \
    else \
        just style; \
    fi
    just lint
    just requirements-lint
    just changelog
    just typecheck
    just test
    just requirements-report
    just docs

# Run tests with coverage
[group("test")]
test:
    {{ uv_run }} pytest -n 4

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

# Validate the repository's generated okfreq requirement layer
[group("lint")]
requirements-lint:
    {{ uv_run }} okfreq lint requirements
    {{ uv_run }} okfreq update-coverage requirements --check

# Generate downloadable requirements traceability artifacts
[group("build")]
requirements-report:
    mkdir -p dist
    {{ uv_run }} okfreq generate-report requirements \
        --output-json dist/requirements-report.json \
        --output-summary-md dist/requirements-report.md

# Run type checkers (ty + mypy)
[group("typecheck")]
typecheck:
    {{ uv_run }} ty check src
    {{ uv_run }} mypy src

# Build Sphinx documentation (regenerates CHANGELOG first, treats warnings as errors)
[group("docs")]
docs:
    just changelog
    {{ uv_run }} sphinx-build -W -b html docs/source docs/_build/html

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
refresh-okf-schema-example:
    {{ uv_run }} okf-schema index --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema lint --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema validate --path examples/ai-llm-knowledge-base --strict
    {{ uv_run }} okf-schema stats --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema list --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema backlinks --path examples/ai-llm-knowledge-base papers/attention-is-all-you-need papers/toolformer

refresh-okfkb-example:
    {{ uv_run }} okfkb init --force examples/specific-hw-knowledge-base/
    {{ uv_run }} okfkb new-finding examples/specific-hw-knowledge-base/ \
        --title "HW Failure investigation" \
        --confidence low \
        --context "Hardware failure pattern observed in production logs during stress testing."
    {{ uv_run }} okfkb update examples/specific-hw-knowledge-base/
    {{ uv_run }} okfkb validate examples/specific-hw-knowledge-base/
    {{ uv_run }} okf-schema validate --strict --path examples/specific-hw-knowledge-base/

refresh-okfreq-examples:
    rm -rf examples/okfreq-examples/requirements/
    {{ uv_run }} okfreq init --force examples/okfreq-examples/requirements/
    test -f examples/okfreq-examples/requirements/tiers/strs/StRS-default-001.md || \
      {{ uv_run }} okfreq new strs "Export a report" --path examples/okfreq-examples/ \
        --description "When export is requested, the reporting capability SHALL provide a portable report." \
        --user-need "Users need a portable report for offline review." \
        --project OKFREQXMP
    test -f examples/okfreq-examples/requirements/tiers/swrs/SwRS-default-001.md || \
      {{ uv_run }} okfreq new swrs "Write CSV output" --path examples/okfreq-examples/ \
        --description "When export is requested, the service SHALL write the report as CSV output." \
        --project OKFREQXMP \
        --derives-from "StRS-default-001"
    {{ uv_run }} python -c 'from pathlib import Path; root=Path("examples/okfreq-examples/requirements/tiers"); p=root/"strs/StRS-default-001.md"; t=p.read_text(); t=t.replace("<!-- Record stakeholder constraints, exclusions, or decisions that shape the\\n     outcome. Remove this section when there are none. -->\\n\\n- <known constraint, exclusion, or rationale>", "The report must remain usable offline and the requirement does not prescribe a specific portable format."); p.write_text(t); p=root/"swrs/SwRS-default-001.md"; t=p.read_text(); t=t.replace("### Scenario: <nominal behavior>\\n\\n- GIVEN <precondition and relevant inputs>\\n- WHEN <trigger or action>\\n- THEN <single observable, verifiable outcome>", "### Scenario: Export selected rows\\n\\n- GIVEN a report containing selected rows\\n- WHEN CSV export is requested\\n- THEN the service returns UTF-8 CSV with one record per selected row"); t=t.replace("### Scenario: <boundary or failure behavior>\\n\\n- GIVEN <boundary precondition or failure>\\n- WHEN <trigger or action>\\n- THEN <observable recovery, rejection, or boundary outcome>", "### Scenario: Export an empty selection\\n\\n- GIVEN a report with no selected rows\\n- WHEN CSV export is requested\\n- THEN the service returns an empty CSV document without failing"); t=t.replace("<!-- Name the verification method, evidence, and boundaries. Do not claim\\n     coverage until implementation and test markers exist. -->\\n\\n- Method: <test, inspection, analysis, or demonstration>\\n- Criteria: <objective pass condition>", "- Method: test\\n- Criteria: Automated tests compare exact CSV output for populated and empty inputs."); p.write_text(t)'
    {{ uv_run }} pytest -q -o addopts='' -p no:cacheprovider examples/okfreq-examples/tests
    {{ uv_run }} okfreq trace examples/okfreq-examples/ --json
    {{ uv_run }} okfreq update-coverage examples/okfreq-examples/ --check
    {{ uv_run }} okfreq update-coverage examples/okfreq-examples/
    {{ uv_run }} okfreq validate examples/okfreq-examples/ --prose
    {{ uv_run }} okfreq lint examples/okfreq-examples/ --prose
    {{ uv_run }} okfreq generate-report examples/okfreq-examples/ \
        --output examples/okfreq-examples/dist/requirements-report.json


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

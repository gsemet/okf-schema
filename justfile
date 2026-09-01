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
    just refresh-all-examples
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
refresh-all-examples:
    just refresh-okf-schema-example
    just refresh-okfkb-example
    just refresh-okfreq-examples

[group("build")]
refresh-okf-schema-example:
    {{ uv_run }} okf-schema index --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema lint --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema validate --path examples/ai-llm-knowledge-base --strict
    {{ uv_run }} okf-schema stats --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema list --path examples/ai-llm-knowledge-base
    {{ uv_run }} okf-schema backlinks --path examples/ai-llm-knowledge-base papers/attention-is-all-you-need papers/toolformer

[group("build")]
refresh-okfkb-example:
    {{ uv_run }} okfkb update examples/okfkb-hw-knowledge-base/
    {{ uv_run }} okfkb validate examples/okfkb-hw-knowledge-base/
    {{ uv_run }} okf-schema validate --strict --path examples/okfkb-hw-knowledge-base/

[group("build")]
refresh-okfreq-examples:
    rm -rf examples/okfreq-examples/requirements/
    {{ uv_run }} okfreq init --force examples/okfreq-examples/requirements/
    {{ uv_run }} python -c 'from pathlib import Path; p=Path("examples/okfreq-examples/requirements/config.yml"); t=p.read_text(); t=t.replace("  default: {source_dirs: [src], test_dirs: [tests]}", "  Core: {id_token: CORE, source_dirs: [src], test_dirs: [tests]}"); assert "  Core: {id_token: CORE, source_dirs: [src], test_dirs: [tests]}" in t; p.write_text(t)'
    test -f examples/okfreq-examples/requirements/tiers/strs/StRS-CORE-001.md || \
        {{ uv_run }} okfreq new strs "Export a report" --path examples/okfreq-examples/ \
            --scope Core \
            --description "When export is requested, the reporting capability SHALL provide a portable report." \
            --user-need "Users need a portable report for offline review." \
            --project OKFREQXMP
    test -f examples/okfreq-examples/requirements/tiers/swrs/SwRS-CORE-001.md || \
        {{ uv_run }} okfreq new swrs "Write CSV output" --path examples/okfreq-examples/ \
            --scope Core \
            --description "When export is requested, the service SHALL write the report as CSV output." \
            --project OKFREQXMP \
            --derives-from "StRS-CORE-001"
    test -f examples/okfreq-examples/requirements/tiers/swrs/SwRS-CORE-002.md || \
        {{ uv_run }} okfreq new swrs "Format Rust CSV rows" --path examples/okfreq-examples/ \
            --scope Core \
            --description "When Rust export is requested, the service SHALL return the selected row as a newline-terminated CSV record." \
            --project OKFREQXMP \
            --derives-from "StRS-CORE-001"
    {{ uv_run }} python -c 'from pathlib import Path; root=Path("examples/okfreq-examples/requirements/tiers"); p=root/"strs/StRS-CORE-001.md"; t=p.read_text(); t=t.replace("<known constraint, exclusion, or rationale>", "The report must remain usable offline and the requirement does not prescribe a specific portable format."); p.write_text(t); p=root/"swrs/SwRS-CORE-001.md"; t=p.read_text(); t=t.replace("<nominal behavior>", "Export selected rows").replace("<precondition and relevant inputs>", "a report containing selected rows").replace("<trigger or action>", "CSV export is requested", 1).replace("<single observable, verifiable outcome>", "the service returns UTF-8 CSV with one record per selected row").replace("<boundary or failure behavior>", "Export an empty selection").replace("<boundary precondition or failure>", "a report with no selected rows").replace("<trigger or action>", "CSV export is requested", 1).replace("<observable recovery, rejection, or boundary outcome>", "the service returns an empty CSV document without failing").replace("<test, inspection, analysis, or demonstration>", "test").replace("<objective pass condition>", "Automated tests compare exact CSV output for populated and empty inputs."); p.write_text(t)'
    {{ uv_run }} python -c 'from pathlib import Path; p=Path("examples/okfreq-examples/requirements/tiers/swrs/SwRS-CORE-002.md"); t=p.read_text(); t=t.replace("<nominal behavior>", "Return a Rust CSV row").replace("<precondition and relevant inputs>", "a Rust report row with two fields").replace("<trigger or action>", "Rust CSV export is requested", 1).replace("<single observable, verifiable outcome>", "the service returns the fields as one newline-terminated CSV record").replace("<boundary or failure behavior>", "Export an empty Rust row").replace("<boundary precondition or failure>", "a Rust report row with two empty fields").replace("<trigger or action>", "Rust CSV export is requested", 1).replace("<observable recovery, rejection, or boundary outcome>", "the service returns a newline-terminated empty CSV record without failing").replace("<test, inspection, analysis, or demonstration>", "test").replace("<objective pass condition>", "The Rust test compares exact output for populated and empty rows."); p.write_text(t)'
    {{ uv_run }} python -c 'import re; from pathlib import Path; root=Path("examples/okfreq-examples/requirements/tiers"); p=root/"strs/StRS-CORE-001.md"; t=p.read_text(); t=re.sub(r"(?m)^uuid: .+$", "uuid: 00000000-0000-4000-8000-000000000001", t, count=1); p.write_text(t); p=root/"swrs/SwRS-CORE-001.md"; t=p.read_text(); t=re.sub(r"(?m)^uuid: .+$", "uuid: 00000000-0000-4000-8000-000000000002", t, count=1); p.write_text(t); p=root/"swrs/SwRS-CORE-002.md"; t=p.read_text(); t=re.sub(r"(?m)^uuid: .+$", "uuid: 00000000-0000-4000-8000-000000000003", t, count=1); p.write_text(t)'
    {{ uv_run }} pytest -q -o addopts='' -p no:cacheprovider examples/okfreq-examples/tests
    {{ uv_run }} okfreq trace examples/okfreq-examples/ --json
    {{ uv_run }} okfreq update-coverage examples/okfreq-examples/
    {{ uv_run }} okfreq update-coverage examples/okfreq-examples/ --check
    {{ uv_run }} okfreq validate examples/okfreq-examples/ --prose
    {{ uv_run }} okfreq lint examples/okfreq-examples/ --prose
    mkdir -p examples/okfreq-examples/dist
    {{ uv_run }} okfreq generate-report examples/okfreq-examples/ \
        --output-json examples/okfreq-examples/dist/requirements-report.json \
        --output-summary-md examples/okfreq-examples/dist/requirements-report.md
    {{ uv_run }} python -c 'import json; import re; from pathlib import Path; fixed_date="2026-09-01T00:00:00+00:00"; report_path=Path("examples/okfreq-examples/dist/requirements-report.json"); report=json.loads(report_path.read_text()); report.pop("bundle_path", None); scan=report.get("scan", {}); scan.pop("project_root", None); report["generated_at"]=fixed_date; report["generated_by"]["version"]="0.0.0-example"; report_path.write_text(json.dumps(report, indent=2) + chr(10)); markdown_path=Path("examples/okfreq-examples/dist/requirements-report.md"); markdown=markdown_path.read_text(); markdown, count=re.subn(r"(?m)^Generated: .*$", "Generated: " + fixed_date, markdown, count=1); assert count == 1; markdown_path.write_text(markdown)'


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

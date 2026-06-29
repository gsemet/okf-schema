# Implementation Plan: okf-schema — Modern Python Package for OKF Bundle Management

## Overview

Create a new open-source Python project `okf-schema` that provides a CLI tool and Python library for working with OKF (Open Knowledge Format) bundles. The project uses a modern Python stack: `uv` for package management, `hatchling` + `hatch-vcs` for building and versioning, `ruff` for linting/formatting, `ty` for type checking, `pytest` for testing, and `Sphinx` for documentation.

The core validation and indexing logic is adapted from existing reference scripts (`validate_okf.py`, `validate_schema.py`, `index_okf.py`) found in `nestor-compendium/skills/Engineering/Knowledge_Graphs/okf/scripts/`, refactored into a clean, testable package with `src/` layout.

## Architecture Changes

This is a greenfield project. The architecture follows a layered design:

1. **Internal layer** (`okf_schema/_internal/`): Data models, YAML helpers, utilities — not part of the public API.
2. **Core engine layer** (`okf_schema/validator.py`, `okf_schema/formatter.py`): Bundle validation and frontmatter formatting logic.
3. **Public API layer** (`okf_schema/api.py`): Clean programmatic interface exposing `validate_bundle`, `format_bundle`, `search_bundle`, `graph_bundle`, `stats_bundle`, `index_bundle`.
4. **CLI layer** (`okf_schema/cli.py`): Click-based CLI with 10 subcommands, delegating to the public API.
5. **Schema layer** (`okf_schema/schemas/`): Built-in minimal OKF schema.

## Implementation Steps

### Step 1: Package Scaffolding & Configuration
**Files to create**:
- `pyproject.toml` — Project metadata, hatchling build backend, hatch-vcs, dependencies, tool configs (ruff, pytest, coverage)
- `src/okf_schema/__init__.py` — Package entry point with `__version__`
- `justfile` — Task automation (preflight, test, style, lint, typecheck, docs, clean)
- `.gitignore` — Python project ignores
- `LICENSE` — MIT (already exists)
- `README.md` — Project overview, quickstart, installation
- `.editorconfig` — Editor consistency
- `CONTRIBUTING.md` — Contribution guidelines

**Technical approach**: Model after `python-extsemver` but modernized. Use `hatch-vcs` for automatic versioning from git tags. Configure `ruff` for linting and import sorting. Set `pytest` with `pytest-cov` for 95% coverage. Use `ty` (Astral) for type checking.

**Dependencies**: None (greenfield).

### Step 2: Internal Infrastructure
**Files to create**:
- `src/okf_schema/_internal/__init__.py`
- `src/okf_schema/_internal/models.py` — `Finding`, `Report`, `ConceptInfo` dataclasses
- `src/okf_schema/_internal/yaml.py` — `make_yaml()`, `extract_frontmatter()`, `parse_yaml()` using `ruamel.yaml`
- `src/okf_schema/_internal/utils.py` — `collect_markdown_files()`, `resolve_link()`, `find_broken_links()`, `has_markdown_files()`
- `src/okf_schema/schemas/__init__.py` — Built-in minimal schema (requires `type` string field)

**Technical approach**: Extract reusable helpers from the reference scripts. Use `ruamel.yaml` with `preserve_quotes=True` and `default_flow_style=False`. The built-in schema is a minimal JSON Schema validating frontmatter has a non-empty `type` field.

**Dependencies**: Step 1.

### Step 3: Bundle Validator Core
**Files to create/modify**:
- `src/okf_schema/validator.py` — Core validation functions

**Technical approach**: Refactor `validate_okf.py` into clean functions:
- `validate_concept()` — E1, E2, E4, W1, W2, W3, W6
- `validate_index()` — E3 (frontmatter check for non-root index.md)
- `validate_log()` — E3 (no frontmatter), W5 (ISO 8601 date headings)
- `validate_bundle()` — Orchestrates all validators, tracks directories, emits W4
- `load_schema_database()` — Loads `.schema.json` / `.schema.yaml` files
- `validate_against_schema()` — Uses `jsonschema.Draft202012Validator`

Add E5 (unflatten list in frontmatter) and E6 (reserved file naming conflict) as new rules not in the original script.

**Dependencies**: Step 2.

### Step 4: Frontmatter Formatter
**Files to create**:
- `src/okf_schema/formatter.py` — Frontmatter formatting logic

**Technical approach**: Use `ruamel.yaml` to parse frontmatter, recursively flatten nested lists while preserving comments and formatting. Support three modes:
- Default: in-place modification
- `--check`: exit 1 if changes needed (no modifications)
- `--diff`: show unified diff instead of modifying

The formatter walks the frontmatter dict and converts any nested list structure to flat lists.

**Dependencies**: Step 2.

### Step 5: Public Python API
**Files to create**:
- `src/okf_schema/api.py` — Public programmatic interface

**Technical approach**: Expose clean functions that wrap the core engine:
- `validate_bundle(bundle_path, schema_db=None) -> Report`
- `format_bundle(bundle_path, check=False, diff=False) -> list[FormattedResult]`
- `search_bundle(bundle_path, query) -> list[SearchResult]`
- `graph_bundle(bundle_path) -> dict[str, list[str]]`
- `stats_bundle(bundle_path) -> BundleStats`
- `index_bundle(bundle_path) -> list[IndexUpdate]`
- `list_bundle(bundle_path) -> list[ConceptSummary]`
- `show_bundle(bundle_path, concept_path) -> ConceptDetail`

Each function handles path resolution, error handling, and returns typed results.

**Dependencies**: Steps 3, 4.

### Step 6: CLI — init, new, validate, format
**Files to create**:
- `src/okf_schema/cli.py` — Click CLI entry point and subcommands

**Technical approach**: Use `click` with a command group. Implement:
- `init <name>` — Create `name/bundle/` (with `index.md`, `log.md`) and `name/schema/`
- `new --path <root> --name <rel-path> [--type <type>] [--title <title>]` — Create concept file with frontmatter template
- `validate <bundle-path> [--schema-db <dir>]` — Run validator, print report, exit 0/1/2
- `format <bundle-path> [--check] [--diff]` — Run formatter

Global options: `--version`, `--verbose`/`-v`, `--quiet`/`-q`.

**Dependencies**: Steps 1, 5.

### Step 7: CLI — list, show, index, search, graph, stats
**Files to modify**:
- `src/okf_schema/cli.py` — Additional subcommands

**Technical approach**: Implement remaining subcommands:
- `list <bundle-path>` — Tabular output: `<path>  <type>  <title>`
- `show <bundle-path> <concept-path>` — YAML frontmatter + body
- `index <bundle-path>` — Regenerate all `index.md` files (adapted from `index_okf.py`)
- `search <bundle-path> <query>` — Case-insensitive substring search across title, description, type, tags
- `graph <bundle-path>` — ASCII adjacency list
- `stats <bundle-path>` — Bundle statistics with bar charts (by type, tags cloud, links)

**Dependencies**: Step 6.

### Step 8: Unit Tests — Validator & Formatter
**Files to create**:
- `tests/__init__.py`
- `tests/test_validator.py` — Tests for all validation rules (E1-E6, W1-W6)
- `tests/test_formatter.py` — Tests for format modes, comment preservation, list flattening
- `tests/fixtures/bundle/` — Test OKF bundles (valid, invalid, edge cases)
- `tests/fixtures/schema/` — Test schema files

**Technical approach**: Use `pytest` with `tmp_path` fixture for filesystem isolation. Test each validation rule individually with dedicated fixture files. Test formatter with files containing nested lists and comments. Target 95% coverage.

**Dependencies**: Steps 3, 4.

### Step 9: Unit Tests — CLI & API
**Files to create**:
- `tests/test_api.py` — Tests for all public API functions
- `tests/test_cli.py` — Tests for all CLI subcommands using `click.testing.CliRunner`

**Technical approach**: Test API functions with fixture bundles. Test CLI commands with `CliRunner.invoke()`, asserting exit codes and output content. Cover edge cases: missing bundle, existing file, bad args, empty bundle.

**Dependencies**: Steps 7, 8.

### Step 10: Sphinx Docs, GitHub Actions CI/CD, and SKILL.md
**Files to create**:
- `docs/source/conf.py` — Sphinx configuration (furo theme, myst-parser, sphinx-click, autodoc)
- `docs/source/index.md` — Documentation landing page
- `docs/source/api.md` — API reference via autodoc
- `docs/source/cli.md` — CLI reference via sphinx-click
- `.github/workflows/ci.yml` — Test matrix (Python 3.10-3.13 on ubuntu; macos + windows for 3.12)
- `.github/workflows/publish.yml` — Trusted publishing to PyPI on release
- `skills/okf-schema/SKILL.md` — Compendium-style skill for agents

**Technical approach**: Configure Sphinx with `furo` theme and `myst-parser` for Markdown. Use `sphinx-click` for CLI docs and `sphinx-autodoc-typehints` for API docs. GitHub Actions uses `just preflight` for the main check job. Trusted publishing requires OIDC configuration on PyPI. SKILL.md follows Compendium format with frontmatter metadata.

**Dependencies**: Steps 1, 9.

## Testing Strategy

- **Unit tests**: Every module has corresponding tests. Validator tests cover all E/W codes. Formatter tests cover all modes. CLI tests cover all subcommands and exit codes.
- **Integration tests**: CLI end-to-end with temporary directories. API integration with full fixture bundles.
- **Manual testing**: Install package in editable mode, run `okf-schema --help`, test each subcommand against a real OKF bundle (e.g., `moulinsart/memory-bank`).

## Risks and Mitigations

- **Risk**: `ruamel.yaml` behavior differences across versions → **Mitigation**: Pin `>=0.18.0`, test with multiple versions
- **Risk**: `ty` (Astral type checker) may have limited compatibility or availability → **Mitigation**: Also include `mypy` as fallback in dev dependencies
- **Risk**: Trusted publishing OIDC setup on PyPI requires manual configuration → **Mitigation**: Document setup steps in README, test with TestPyPI first
- **Risk**: Windows path handling in tests → **Mitigation**: Use `pathlib.Path` everywhere, test on Windows in CI

## Rollout Considerations

- This is a new PyPI package — no backward compatibility concerns.
- First release should be `v0.1.0` tag to trigger `hatch-vcs` versioning.
- GitHub repository must enable OIDC trusted publishing with PyPI before first release.

## Requirements Impact

No requirement traceability applicable to this change.

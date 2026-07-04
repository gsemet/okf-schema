# MR Description — okf-schema-kb-subcommands

## Summary

Add a `kb` subcommand group to the `okf-schema` CLI plus a standalone `okfkb`
alias for knowledge-base management.

## What Changed

### New Commands
- `okfkb init [PATH]` — Scaffold a new knowledge-base bundle with 8 YAML
  schemas, 8 content directories, `index.md`, and `log.md`.
- `okfkb install [PATH]` — Install bundled KB skills and guidelines into a
  target project, patching or creating `AGENTS.md`.
- `okf-schema init --pattern kb` — Extensible init pattern backed by
  `INIT_PATTERNS` registry.

### Bundled Assets (13 files)
| Asset | Count | Location |
|-------|-------|----------|
| KB schema YAML files | 8 | `src/okf_schema/data/kb/_schema/` |
| Skills | 2 | `src/okf_schema/data/kb/skills/` |
| Guideline | 1 | `src/okf_schema/data/kb/guidelines/` |

### New Modules
- `src/okf_schema/kb/__init__.py`
- `src/okf_schema/kb/cli.py` — Click command group
- `src/okf_schema/kb/scaffold.py` — `scaffold_kb()`
- `src/okf_schema/kb/install.py` — `install_kb()`
- `src/okf_schema/kb/patterns.py` — `INIT_PATTERNS` registry

### New Tests (69 KB-specific, 463 total)
- `tests/test_kb_scaffold.py` — 25 tests, 100% coverage
- `tests/test_kb_install.py` — 21 tests, 100% coverage
- `tests/test_kb_patterns.py` — 5 tests, 100% coverage
- `tests/test_kb_cli.py` — 18 tests, 100% coverage

### Modified Files
- `src/okf_schema/cli.py` — Register `kb` group, add `--pattern` flag
- `pyproject.toml` — Add `okfkb` console-scripts entry point
- `README.md` — Add Knowledge Base documentation section
- `docs/source/reference/kb-commands.md` — New reference page
- `docs/source/index.rst` — Add kb-commands to toctree

## Quality Gates

| Gate | Result |
|------|--------|
| `just preflight` | 463 passed, 96.55% coverage (threshold 96%) |
| `just typecheck` | ty + mypy clean (17 source files) |
| `just lint` | ruff clean |
| `just style-check` | ruff format clean |

## Backward Compatibility

- `okf-schema init <name>` (no `--pattern`) behaves identically to before.
- No breaking changes to existing CLI commands or APIs.

## Rediscover ALL Commits

> **Reviewer instruction**: This MR squashes **13 commits** into one.
> To review the incremental development history, run:
> ```bash
> git log --oneline a674cdee995ba4e032cd95a0532756a6428ad2d3..HEAD
> ```
> Or inspect the per-task phase reports in:
> `.github/changes/request/okf-schema-kb-subcommands/06-phase-report-*.md`

## Checklist

- [x] `just preflight` passes locally
- [x] Tests added for new functionality
- [x] Documentation updated (README + Sphinx)
- [x] No breaking changes
- [x] Coverage threshold met (96.55% >= 96%)

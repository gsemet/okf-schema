# READ BEFORE — okf-schema Project

## Change Summary

Create a new open-source Python project `okf-schema` that provides a CLI tool and Python library for working with **OKF (Open Knowledge Format)** bundles. OKF is a markdown-based knowledge format where each concept is a markdown file with YAML frontmatter.

**JIRA**: N/A (Open-source project)
**PRD**: `.agents/changes/request/init/`
**Specification**: `03-specification.md`
**Initial SHA**: `a16eb8ab7185606e5cb60730c46ad8e52f71d2f3`

## Key Files / Modules

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, build backend, dependencies, tool configs |
| `justfile` | Task automation (preflight, test, style, lint, typecheck, docs) |
| `src/okf_schema/__init__.py` | Package entry point |
| `src/okf_schema/_internal/models.py` | Dataclasses: `Finding`, `Report`, `ConceptInfo` |
| `src/okf_schema/_internal/yaml.py` | YAML helpers using `ruamel.yaml` |
| `src/okf_schema/_internal/utils.py` | Shared utilities (file collection, link resolution) |
| `src/okf_schema/schemas/__init__.py` | Built-in minimal OKF schema |
| `src/okf_schema/validator.py` | Bundle validation engine (E1-E6, W1-W6) |
| `src/okf_schema/formatter.py` | Frontmatter formatting (list flattening) |
| `src/okf_schema/api.py` | Public Python API |
| `src/okf_schema/cli.py` | Click CLI with 10 subcommands |
| `tests/` | pytest test suite with fixtures |
| `docs/source/` | Sphinx documentation |
| `.github/workflows/` | GitHub Actions CI/CD |
| `skills/okf-schema/SKILL.md` | Compendium-style agent skill |

## Reference Scripts

The core validation logic is adapted from these existing scripts (read for reference, do not copy verbatim):
- `nestor-compendium/skills/Engineering/Knowledge_Graphs/okf/scripts/validate_okf.py`
- `nestor-compendium/skills/Engineering/Knowledge_Graphs/okf/scripts/validate_schema.py`
- `nestor-compendium/skills/Engineering/Knowledge_Graphs/okf/scripts/index_okf.py`

## Project Rules & Guidelines

All tasks in this change MUST comply with the following project rules.
Read each file before coding and keep it open during implementation.

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.pytest.ini_options] | Test configuration | `tests/` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |
| `AGENTS.md` (if created) | Project conventions | Everything |

> The Task Inspector **will verify compliance** with every rule listed here.

## Commit Message Guideline

**Source**: No project-specific commit convention found — use conventional commits.

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: add <description>` — new features
- `fix: correct <description>` — bug fixes
- `docs: update <description>` — documentation
- `test: add tests for <description>` — tests
- `chore: <description>` — maintenance
- `ci: <description>` — CI/CD changes

Add the planning commit trailer to all planning-phase commits:
```
Craftsman-Commit-Type: Planning
```

## Preflight Command

Run the full quality gate before marking any task done:
```bash
just preflight
```

This runs: format check → lint → typecheck → test with coverage.

## Coding Principles

1. **Think before coding** — Understand the specification and existing code before making changes.
2. **Simplicity first** — Prefer simple, readable solutions over clever ones.
3. **Surgical changes** — Make the smallest change that achieves the objective.
4. **Goal-driven execution** — Every line of code should serve the task's acceptance criteria.

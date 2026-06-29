## Summary

This MR delivers `okf-schema`, a new open-source Python package providing a CLI
tool and Python library for working with **OKF (Open Knowledge Format)** bundles.

### What changed

- **Package scaffolding** (`pyproject.toml`, `src/` layout, `justfile`, `uv.lock`)
- **Internal infrastructure** (`_internal/models.py`, `yaml.py`, `utils.py`,
  `schemas/__init__.py`)
- **Bundle validator** (`validator.py`) — E1–E6 errors + W1–W6 warnings
- **Frontmatter formatter** (`formatter.py`) — list flattening with comment
  preservation via `ruamel.yaml` round-trip
- **Public Python API** (`api.py`) — 8 typed functions for programmatic use
- **Click CLI** (`cli.py`) — 10 subcommands with global `--version`, `--verbose`,
  `--quiet` options
- **298 tests** across unit, integration, and edge-case suites — 96.43 % coverage
- **Sphinx documentation** with furo theme, autodoc, napoleon, and CLI reference
- **GitHub Actions CI/CD** — cross-platform test matrix + OIDC trusted publishing
  to PyPI
- **Compendium SKILL.md** for agent consumption

### Commits

| SHA | Message |
|:----|:--------|
| `f0aeea9` | plan: generate implementation plan and task breakdown for okf-schema |
| `8ccb1fd` | feat: scaffold okf-schema package with pyproject.toml and justfile |
| `76d6329` | feat: add internal infrastructure models, yaml helpers, and built-in schema |
| `3573410` | feat: implement bundle validator with E1-E6 and W1-W6 rules |
| `63febfa` | feat: implement frontmatter formatter with list flattening and diff mode |
| `f7d59ef` | feat(api): add public Python API for OKF bundle operations |
| `00ab6f3` | feat: add CLI entry point with init, new, validate, format subcommands |
| `0b8d302` | feat: add list, show, index, search, graph, stats CLI subcommands |
| `74ecd66` | test: add integration tests and edge case coverage |
| `5e9a896` | docs: add Sphinx docs, GitHub Actions CI/CD, and agent SKILL.md |
| `98f4908` | docs: add Sphinx docs, GitHub Actions CI/CD, and agent SKILL.md (after review) |

### Test results

- **298 passed** — 96.43 % coverage (exceeds 95 % minimum)
- Style-check, lint, typecheck (`ty` + `mypy`) all clean
- `just preflight` passes end-to-end

<!-- COST_PLACEHOLDER -->

## Checklist

- [x] `just preflight` passes locally
- [x] Tests added for all new functionality
- [x] Documentation updated (`docs/source/`, `README.md`, `CONTRIBUTING.md`)
- [x] CI/CD workflows validated (`.github/workflows/ci.yml`, `publish.yml`)
- [x] No `TODO` / `FIXME` / `HACK` comments introduced
- [x] Conventional commit format followed

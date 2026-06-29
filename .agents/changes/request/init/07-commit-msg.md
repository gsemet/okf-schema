feat: create okf-schema — Modern Python Package for OKF Bundle Management

This delivery introduces `okf-schema`, a comprehensive CLI tool and Python
library for working with OKF (Open Knowledge Format) bundles.

Highlights:

- Package scaffolding with pyproject.toml, src/ layout, hatchling + hatch-vcs,
  ruff, ty, mypy, pytest, and just task runner
- Internal infrastructure: models, YAML helpers (ruamel.yaml round-trip),
  utilities, and built-in JSONSchema
- Bundle validator enforcing E1–E6 conformance errors and W1–W6 best-practice
  warnings (missing frontmatter, schema validation, broken links, etc.)
- Frontmatter formatter with recursive list flattening, check/diff/in-place
  modes, and comment preservation
- Public Python API: validate_bundle, format_bundle, list_bundle, show_bundle,
  index_bundle, search_bundle, graph_bundle, stats_bundle
- Click CLI with 10 subcommands: init, new, validate, format, list, show,
  index, search, graph, stats
- 298 tests reaching 96.43 % coverage (exceeds 95 % minimum)
- Sphinx documentation with furo theme, autodoc, and CLI reference
- GitHub Actions CI/CD: test matrix (Python 3.10–3.13) and OIDC trusted
  publishing to PyPI
- In-project Compendium-style SKILL.md for agent guidance

<!-- COST_PLACEHOLDER -->

Craftsman-Commit-Type: Finalization

# Request: Create okf-schema — Modern Python Package for OKF Bundle Management

## Context

Create a new open-source Python project in `/Users/az02065/Projects/DevTools/okf-schema` that provides a CLI tool and Python library for working with **OKF (Open Knowledge Format)** bundles. The project will be published to **PyPI** (not internal Artifactory) under the name `okf-schema`.

The core logic is adapted from existing scripts found in `nestor-compendium/skills/Engineering/Knowledge_Graphs/okf/scripts/` (`validate_okf.py`, `validate_schema.py`), refactored into a clean, modern Python package.

The project is modeled after `python-extsemver` (uv + pyproject.toml + just + pytest + Sphinx) but modernized with current best practices.

## Desired Outcome

A fully functional, well-tested Python package with:
- A comprehensive CLI for OKF bundle operations
- A public Python API for programmatic use
- PyPI-ready packaging with trusted publishing
- Sphinx documentation with API and CLI reference
- A Compendium-style SKILL.md for agent guidance

## Scope

### In Scope
- Package scaffolding (pyproject.toml, src/ layout, tests, docs)
- CLI with 9 subcommands: `init`, `new`, `validate`, `format`, `list`, `show`, `index`, `search`, `graph`, `stats`
- Python API exposing core validation and formatting functions
- Built-in minimal OKF schema for basic frontmatter validation
- GitHub Actions CI/CD (test matrix + trusted publishing to PyPI)
- Sphinx documentation (API reference via autodoc, CLI reference)
- In-project Compendium-style SKILL.md
- CONTRIBUTING.md and .editorconfig

### Out of Scope
- Web UI or server component
- External database integration
- Real-time collaboration features

## Resolved Decisions

| # | Topic | Resolution |
|---|-------|------------|
| 1 | Package name | `okf-schema` |
| 2 | Target directory | `/Users/az02065/Projects/DevTools/okf-schema` |
| 3 | Python version | `>=3.10` |
| 4 | License | MIT |
| 5 | Build backend | `hatchling` |
| 6 | Versioning | Automatic from git tags (`hatch-vcs`) |
| 7 | Lint/format | `ruff` |
| 8 | Type checker | `ty` (Astral) |
| 9 | Test framework | `pytest` |
| 10 | Coverage target | 95% |
| 11 | Task runner | `just` |
| 12 | CI/CD | GitHub Actions |
| 13 | PyPI publishing | Trusted publishing (OIDC) |
| 14 | Package layout | `src/` layout (`src/okf_schema/`) |
| 15 | Author | Gaetan Semet <gaetan@xeberon.net> |
| 16 | GitHub repo | `https://github.com/gsemet/okf-schema` |
| 17 | PyPI description | "Open Knowledge Format with JSONSchema" |
| 18 | Pre-commit hooks | No |
| 19 | Extra files | `CONTRIBUTING.md`, `.editorconfig` |
| 20 | Code origin | Adapted/refactored from existing scripts |
| 21 | Runtime dependencies | `ruamel.yaml>=0.18.0`, `jsonschema>=4.23.0` |
| 22 | Built-in schema | Yes — minimal built-in OKF schema |
| 23 | Schema examples | Both documentation and test fixtures |
| 24 | Docs | Sphinx with API + CLI reference |
| 25 | Main just command | `just preflight` |
| 26 | Bundle init structure | `okf-schema init kb` → `kb/bundle/` + `kb/schema/` |
| 27 | In-project skill | Yes — Compendium-style `SKILL.md` |

## Inferred Decisions (Previously Unresolved)

| # | Topic | Inferred Resolution | Rationale |
|---|-------|---------------------|-----------|
| I1 | PyPI keywords/classifiers | `Development Status :: 4 - Beta`, `Intended Audience :: Developers`, `License :: OSI Approved :: MIT License`, `Programming Language :: Python :: 3`, `Programming Language :: Python :: 3.10`, `Programming Language :: Python :: 3.11`, `Programming Language :: Python :: 3.12`, `Programming Language :: Python :: 3.13`, `Topic :: Software Development :: Libraries :: Python Modules`, `Topic :: Text Processing :: Markup` | Standard classifiers for a modern Python CLI/library tool |
| I2 | `new` subcommand interactivity | Flags-only (`--path`, `--name`, `--type`, `--title`). If required flags are missing, print usage and exit with code 2. No interactive prompts. | Keeps CLI scriptable and predictable |
| I3 | `graph` ASCII output format | Simple adjacency list: each concept on its own line, followed by indented outgoing links. Example: `concept-a\n  → concept-b\n  → concept-c` | Simple, readable, works in any terminal |
| I4 | `search` result format | Tabular output with columns: `Path`, `Type`, `Title`. Sorted by path. One row per matching concept. | Clear and compact |
| I5 | `index` regeneration scope | Overwrite existing `index.md` files completely (regenerate from current bundle state). Preserve `log.md` untouched. | Ensures index is always current |
| I6 | `format` dry-run mode | Support `--check` (exit 1 if changes needed), `--diff` (show diff), and default in-place modification. | Follows convention of black, ruff, etc. |
| I7 | Dev dependency completeness | `pytest`, `pytest-cov`, `pytest-mock`, `pytest-xdist`, `ruff`, `ty`, `mypy` (fallback), `sphinx`, `sphinx-autodoc-typehints`, `sphinx-click`, `furo`, `myst-parser` | Modern, comprehensive dev stack |
| I8 | GitHub Actions matrix | Test on Python 3.10, 3.11, 3.12, 3.13 on `ubuntu-latest`. Also test on `macos-latest` and `windows-latest` for Python 3.12 only. | Broad compatibility without excessive CI time |
| I9 | `stats` exact metrics | Use the user's provided example as canonical: Bundle root, Total files, Concepts, No frontmatter, Total size, By Type (with bar chart), Tags Cloud (with bar chart), Links (total + broken) | User-provided example is the specification |

## CLI Specification

### Global Options
- `--version`: Show version and exit
- `--verbose` / `-v`: Increase verbosity (can be repeated)
- `--quiet` / `-q`: Suppress non-error output

### Subcommands

#### `init <name>`
Initialize a new OKF bundle.
- Creates `<name>/bundle/` with `index.md` and `log.md`
- Creates `<name>/schema/` directory (empty)
- Exits 0 on success, 1 if directory already exists

#### `new --path <root> --name <relative-path> [--type <type>] [--title <title>]`
Create a new concept file.
- `<root>`: Path to bundle root (contains `bundle/` and `schema/`)
- `<relative-path>`: Relative path within bundle (e.g., `concepts/ideas`)
- Creates `<root>/bundle/<relative-path>.md` with frontmatter template
- Frontmatter template includes: `type`, `title`, `description`, `tags: []`
- Exits 0 on success, 1 if file already exists, 2 on bad args

#### `validate <bundle-path> [--schema-db <schema-dir>]`
Validate bundle structure and frontmatter.
- Checks all rules from the existing scripts (E1–E6, W1–W6)
- E5 (unflatten list) is an error
- Prints findings grouped by file
- Exits 0 if conformant, 1 if errors, 2 on usage error

#### `format <bundle-path> [--check] [--diff]`
Format frontmatter in all concept files.
- Flattens nested lists in frontmatter while preserving comments
- Default: modify files in-place
- `--check`: exit 1 if any file would change
- `--diff`: show diff instead of modifying
- Uses `ruamel.yaml` to preserve comments and formatting

#### `list <bundle-path>`
List all concepts in the bundle.
- Output: one concept per line, format: `<relative-path>  <type>  <title>`
- Sorted by path

#### `show <bundle-path> <concept-path>`
Display a single concept.
- `<concept-path>`: Relative path within bundle (e.g., `concepts/ideas`)
- Output: frontmatter as YAML, then body markdown

#### `index <bundle-path>`
Auto-regenerate `index.md` files.
- For each directory in `bundle/`, create or overwrite `index.md`
- Index contains: directory title, list of child concepts with links, list of subdirectories with links
- Preserves existing `log.md` files

#### `search <bundle-path> <query>`
Search across concept frontmatter.
- Searches: `title`, `description`, `type`, `tags`
- Case-insensitive substring match
- Output: table with `Path`, `Type`, `Title`

#### `graph <bundle-path>`
Output concept link graph.
- ASCII adjacency list format
- One line per concept, indented outgoing links

#### `stats <bundle-path>`
Bundle statistics.
- Output format matches the user's provided example exactly
- Metrics: root path, total files, concepts, no frontmatter, total size, by type (with bars), tags cloud (with bars), links (total + broken)

## Validation Rules

| Code | Severity | Description |
|------|----------|-------------|
| E1 | Error | Missing or unparseable YAML frontmatter |
| E2 | Error | Missing or empty `type` field |
| E3 | Error | Reserved file (`index.md`, `log.md`) has unexpected structure |
| E4 | Error | Schema validation failure (when schema DB provided) |
| E5 | Error | Unflatten list in frontmatter |
| W1 | Warning | Missing recommended field `title` or `description` |
| W2 | Warning | Broken cross-link |
| W3 | Warning | Missing `timestamp` field |
| W4 | Warning | Directory missing `index.md` |
| W5 | Warning | `log.md` date headings not ISO 8601 |
| W6 | Warning | Schema database file not found for declared type |

## Project Structure

```
okf-schema/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Test + lint + typecheck on push/PR
│       └── publish.yml     # Trusted publishing to PyPI on release
├── docs/
│   ├── source/
│   │   ├── conf.py
│   │   ├── index.md
│   │   ├── api.md
│   │   └── cli.md
│   └── _build/
├── src/
│   └── okf_schema/
│       ├── __init__.py
│       ├── cli.py          # Click CLI entry point
│       ├── api.py          # Public Python API
│       ├── validator.py    # Bundle validation logic
│       ├── formatter.py    # Frontmatter formatting
│       ├── schemas/
│       │   └── __init__.py # Built-in minimal schema
│       └── _internal/
│           ├── __init__.py
│           ├── models.py   # Dataclasses
│           ├── yaml.py     # YAML helpers (ruamel)
│           └── utils.py    # Shared utilities
├── tests/
│   ├── __init__.py
│   ├── test_validator.py
│   ├── test_formatter.py
│   ├── test_cli.py
│   └── fixtures/
│       ├── bundle/
│       └── schema/
├── skills/
│   └── okf-schema/
│       └── SKILL.md        # Compendium-style skill
├── .editorconfig
├── .gitignore
├── CONTRIBUTING.md
├── justfile
├── LICENSE
├── pyproject.toml
├── README.md
└── uv.lock
```

## Dependencies

### Runtime
- `ruamel.yaml>=0.18.0`
- `jsonschema>=4.23.0`
- `click>=8.0` (for CLI)

### Development
- `pytest`
- `pytest-cov`
- `pytest-mock`
- `pytest-xdist`
- `ruff`
- `ty`
- `sphinx`
- `sphinx-autodoc-typehints`
- `sphinx-click`
- `furo`
- `myst-parser`

## Just Commands

| Command | Description |
|---------|-------------|
| `just preflight` | Run full validation: format check → lint → typecheck → test with coverage |
| `just test` | Run pytest with coverage |
| `just style` | Format code with ruff |
| `just lint` | Run ruff check |
| `just typecheck` | Run ty |
| `just docs` | Build Sphinx docs |
| `just docs-serve` | Serve docs locally |
| `just clean` | Clean build artifacts |

## GitHub Actions

### CI Workflow (`ci.yml`)
- Trigger: push to `main`, pull requests
- Jobs:
  1. `preflight`: Run `just preflight` on Python 3.10–3.13 (ubuntu-latest)
  2. `cross-platform`: Run tests on macos-latest and windows-latest (Python 3.12 only)

### Publish Workflow (`publish.yml`)
- Trigger: release published
- Job: Build wheel + sdist, publish to PyPI via trusted publishing (OIDC)
- Requires: `preflight` job to pass

## Notes

- The existing scripts (`validate_okf.py`, `validate_schema.py`) should be used as reference for validation logic but refactored into clean, testable functions.
- The `ruamel.yaml` library must be used for all YAML operations to preserve comments during formatting.
- The built-in minimal schema should validate that frontmatter contains at minimum: `type` (string).
- The SKILL.md should follow the Compendium format with frontmatter metadata and structured instructions for agents.

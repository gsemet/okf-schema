# Task 01: Package Scaffolding & Configuration

**Depends on**: None
**Estimated complexity**: Medium
**Type**: Feature
**Phase**: Phase 1 — Package Scaffolding & Core Infrastructure

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.pytest.ini_options] | Test configuration | `tests/` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Create the foundational project structure: `pyproject.toml`, `justfile`, `.gitignore`, `README.md`, `.editorconfig`, `CONTRIBUTING.md`, and the package root `src/okf_schema/__init__.py` with `__version__` using `hatch-vcs`.

## Files to Modify/Create
- `pyproject.toml`
- `justfile`
- `.gitignore`
- `README.md`
- `.editorconfig`
- `CONTRIBUTING.md`
- `src/okf_schema/__init__.py`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 01 --status in_progress --started-at now`
2. Create `pyproject.toml` with:
   - `[project]`: name=`okf-schema`, dynamic version, author=Gaetan Semet, MIT license, Python >=3.10
   - `[project.scripts]`: `okf-schema = "okf_schema.cli:cli"`
   - Dependencies: `ruamel.yaml>=0.18.0`, `jsonschema>=4.23.0`, `click>=8.0`
   - Dev dependencies: `pytest`, `pytest-cov`, `pytest-mock`, `pytest-xdist`, `ruff`, `ty`, `mypy`, `sphinx`, `sphinx-autodoc-typehints`, `sphinx-click`, `furo`, `myst-parser`
   - `[build-system]`: `hatchling` + `hatch-vcs`
   - `[tool.ruff]`: line-length 100, select common rules
   - `[tool.pytest.ini_options]`: testpaths=`tests/`, addopts with coverage
   - `[tool.coverage.run]`: source=`src/okf_schema`, branch=true
   - `[tool.coverage.report]`: fail_under=95
3. Create `justfile` with commands: `preflight`, `test`, `style`, `lint`, `typecheck`, `docs`, `docs-serve`, `clean`
   - `preflight` runs: `style-check`, `lint`, `typecheck`, `test`
   - Use `uv run --no-sync --` prefix for all tool invocations
4. Create `.gitignore` for Python projects (`.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `dist/`, `build/`, `docs/_build/`, `.mypy_cache/`, `.ruff_cache/`)
5. Update `README.md` with project description, installation (`pip install okf-schema`), quickstart example, and link to docs
6. Create `.editorconfig` with standard Python settings (utf-8, lf, indent_size=4 for `.py`)
7. Create `CONTRIBUTING.md` with setup instructions (`just dev`, `just preflight`), coding standards, and PR process
8. Create `src/okf_schema/__init__.py` with `__version__` loaded via `importlib.metadata.version("okf_schema")`
9. Run `uv sync` to generate `uv.lock`
10. Run `just preflight` and fix any issues
11. Update `progress.json` via CLI:
    `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 01 --status coded_not_reviewed --completed-at now`
12. Commit with a conventional commit message:
    `feat: scaffold okf-schema package with pyproject.toml and justfile`

## Acceptance Criteria
- [ ] `pyproject.toml` has correct metadata, dependencies, and tool configs
- [ ] `just preflight` runs without errors (may have no tests yet)
- [ ] `src/okf_schema/__init__.py` exports `__version__`
- [ ] `uv sync` completes successfully
- [ ] README, CONTRIBUTING, and .editorconfig are present and complete
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
<!-- No automated test required for this task type (pure config/scaffolding). -->
<!-- Manual verification: `uv sync`, `just preflight`, `python -c "import okf_schema; print(okf_schema.__version__)"` -->

## Notes
- Model `pyproject.toml` after `python-extsemver` but modernized (ruff instead of black/isort/flake8, ty instead of mypy as primary)
- The `hatch-vcs` version requires a git tag to produce a real version; without tags it returns `0.0.0` — this is expected

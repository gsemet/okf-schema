## INSPECTOR FEEDBACK (Full History)

**Status**: Incomplete - Requires rework

### Round 1 — ❌ FAIL — 2026-06-25T09:57:41Z

**What was done correctly:**
- Sphinx docs (`docs/source/conf.py`, `index.md`, `api.md`, `cli.md`) are well-structured, use the furo theme, include all required extensions, and build without warnings.
- CI workflow (`.github/workflows/ci.yml`) correctly runs `just preflight` on Python 3.10–3.13 (ubuntu) and 3.12 (macos, windows).
- SKILL.md follows Compendium format with proper frontmatter, all 10 CLI subcommands, E1–E6/W1–W6 validation rules, Python API examples, and agent tips.
- Commit message follows conventional commit format.
- Quality gate (`just preflight`) passed: 298 tests, all lint/type checks clean.

**What is WRONG:**
- **`.github/workflows/publish.yml` is functionally broken.** The `publish` job declares `needs: preflight`, and the workflow defines a `preflight` job that calls the CI workflow via `uses: ./.github/workflows/ci.yml`. However, `.github/workflows/ci.yml` **does not declare a `workflow_call` trigger** — it only has `push` and `pull_request` triggers. GitHub Actions will reject this at parse time, meaning the publish workflow will **fail on every release**.

**Fix required:**
Add `workflow_call:` to the `on:` section of `.github/workflows/ci.yml` so it can be invoked as a reusable workflow from `publish.yml`.

---

# Task 09: Sphinx Docs, GitHub Actions CI/CD, and SKILL.md

**Depends on**: Task 01, Task 08
**Estimated complexity**: Medium
**Type**: Documentation
**Phase**: Phase 4 — Tests, Docs, CI/CD & Skill

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Create Sphinx documentation, GitHub Actions CI/CD workflows, and the Compendium-style SKILL.md.

## Files to Modify/Create
- `docs/source/conf.py`
- `docs/source/index.md`
- `docs/source/api.md`
- `docs/source/cli.md`
- `.github/workflows/ci.yml`
- `.github/workflows/publish.yml`
- `skills/okf-schema/SKILL.md`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 09 --status in_progress --started-at now`
2. Create `docs/source/conf.py`:
   - Use `furo` theme
   - Extensions: `sphinx.ext.autodoc`, `sphinx.ext.napoleon`, `sphinx_click`, `sphinx_autodoc_typehints`, `myst_parser`
   - `sys.path.insert` for `src/` directory
   - Project metadata from `okf_schema.__version__`
3. Create `docs/source/index.md`:
   - Title: "okf-schema Documentation"
   - Brief description of the project
   - Toctree with `api.md` and `cli.md`
   - Quickstart section
4. Create `docs/source/api.md`:
   - Use `automodule` for `okf_schema.api`
   - Document all public functions with autodoc
5. Create `docs/source/cli.md`:
   - Use `sphinx-click` directive for `okf_schema.cli:cli`
   - Auto-generate CLI reference from click commands
6. Create `.github/workflows/ci.yml`:
   - Trigger: push to `main`, pull requests
   - Job `preflight`: runs on `ubuntu-latest` with Python 3.10, 3.11, 3.12, 3.13
   - Job `cross-platform`: runs on `macos-latest` and `windows-latest` with Python 3.12 only
   - Steps: checkout, setup Python, install uv, `uv sync`, `just preflight`
7. Create `.github/workflows/publish.yml`:
   - Trigger: release published
   - Job `publish`: depends on `preflight` job
   - Steps: checkout, setup Python, install uv, `uv build`
   - Use `pypa/gh-action-pypi-publish@release/v1` with OIDC trusted publishing
   - Environment: `pypi` with `url: https://pypi.org/p/okf-schema`
8. Create `skills/okf-schema/SKILL.md`:
   - Frontmatter with metadata:
     ```yaml
     ---
     name: okf-schema
     description: CLI and Python library for OKF bundle management
     keywords: [okf, knowledge-format, markdown, yaml, validation, cli]
     ---
     ```
   - Sections:
     - Overview: what okf-schema does
     - Installation: `pip install okf-schema`
     - Quickstart: init, new, validate workflow
     - CLI Reference: brief description of each subcommand
     - Python API: example usage of `okf_schema.api`
     - Validation Rules: table of E1-E6 and W1-W6
     - Tips for Agents: common patterns when working with OKF bundles
9. Verify `just docs` builds without warnings
10. Verify `just docs-serve` serves docs locally
11. Run `just preflight` and fix any issues
12. Update `progress.json` via CLI:
    `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 09 --status coded_not_reviewed --completed-at now`
13. Commit with a conventional commit message:
    `docs: add Sphinx docs, GitHub Actions CI/CD, and agent SKILL.md`

## Acceptance Criteria
- [ ] `docs/source/conf.py` configures Sphinx with furo theme and required extensions
- [ ] `just docs` builds HTML documentation without warnings
- [ ] API reference documents all public functions from `okf_schema.api`
- [ ] CLI reference documents all 10 subcommands
- [ ] `.github/workflows/ci.yml` runs `just preflight` on Python 3.10-3.13 (ubuntu) and 3.12 (macos, windows)
- [ ] `.github/workflows/publish.yml` builds and publishes to PyPI via trusted publishing on release
- [ ] `skills/okf-schema/SKILL.md` follows Compendium format with frontmatter and structured sections
- [ ] SKILL.md includes all validation rules and CLI subcommands
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
<!-- No automated test required for this task type (docs, CI, skill). -->
<!-- Manual verification: `just docs`, inspect HTML output, validate workflow syntax with actionlint if available -->

## Notes
- For GitHub Actions, use the `astral-sh/setup-uv` action to install uv
- The trusted publishing setup requires configuring the PyPI project to trust the GitHub repository — document this in README.md
- SKILL.md should be written in a way that helps AI agents understand how to use okf-schema for OKF bundle operations
- Ensure `docs/source/index.md` uses MyST Markdown syntax (compatible with `myst_parser`)
- The `sphinx-click` extension requires the CLI to be importable — ensure `src/` is in PYTHONPATH during doc build

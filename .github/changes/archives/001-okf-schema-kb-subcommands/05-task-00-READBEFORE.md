# READ BEFORE — okf-schema-kb-subcommands

## Change Summary

Add a `kb` subcommand group to `okf-schema` CLI plus a standalone `okfkb` alias.
Implements two commands: `okfkb init [PATH]` (scaffolds KB folder layout with 8
YAML schemas + 8 dirs + index.md + log.md using bundled importlib.resources data)
and `okfkb install [PATH]` (deploys bundled skills + guideline into target project,
patches AGENTS.md). Extends `okf-schema init` with `--pattern kb` flag. New
subpackage at `src/okf_schema/kb/`.

## Key Files

| File | Role |
|------|------|
| `src/okf_schema/cli.py` | Top-level Click CLI — register `kb` group, add `--pattern` to `init` |
| `src/okf_schema/kb/cli.py` | Click command group for `kb` subcommands |
| `src/okf_schema/kb/scaffold.py` | `scaffold_kb()` — creates dirs, copies schemas, writes index.md/log.md |
| `src/okf_schema/kb/install.py` | `install_kb()` — deploys skills/guidelines, patches AGENTS.md |
| `src/okf_schema/kb/patterns.py` | `INIT_PATTERNS` registry dict for extensible init patterns |
| `src/okf_schema/data/kb/` | Bundled assets (schemas, skills, guidelines) loaded via `importlib.resources` |
| `pyproject.toml` | Entry points (`okfkb`), hatchling include rules |
| `tests/test_kb_*.py` | Unit and integration tests for kb subpackage |

## Project Rules & Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: **96%** (`--cov-fail-under=96`) |
| `pyproject.toml` | Line length: **100** chars |
| `pyproject.toml` | Docstring convention: **Google** |
| `pyproject.toml` | Type checking: `mypy` strict (`disallow_untyped_defs=true`) |
| `AGENTS.md` | Quality gate: `just preflight` (style-check → lint → changelog → typecheck → test → refresh-examples) |
| `AGENTS.md` | Commit convention: **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`) |
| `AGENTS.md` | Python 3.10+, Click, ruamel.yaml, jsonschema |
| `CONTRIBUTING.md` | Minimum coverage: 95% (note: pyproject.toml says 96%, use 96%) |

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(kb): add scaffold_kb function`
- `feat(cli): register kb subcommand group`
- `feat(cli): add --pattern flag to init command`
- `test(kb): add scaffold and install tests`
- `docs: add kb-commands documentation page`
- `chore: bundle KB schema and skill assets`

## Coding Principles

- **TDD (red-green)**: write the failing test first, then implement.
- **Type safety**: all new functions fully typed; mypy strict must pass.
- **Coverage**: every new code path must be exercised by tests.
- **importlib.resources**: use `files("okf_schema.data.kb")` (Python 3.9+ API);
  no `pkg_resources` or `__file__` path manipulation.
- **Backward compatibility**: existing `okf-schema init <name>` must behave
  identically when `--pattern` is omitted.
- **Idempotency**: `AGENTS.md` patching must not duplicate references.

## Boot Sequence for Each Task

1. Read this file (`05-task-00-READBEFORE.md`).
2. Read `03-specification.md` for full requirements.
3. Read `04-plan.md` for technical approach.
4. Read the task file you are executing.
5. Run `just preflight` before and after changes.
6. Update `progress.json` via `craftsman agent update-task` when done.

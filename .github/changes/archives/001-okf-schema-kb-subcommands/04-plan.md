# Implementation Plan — OKF Knowledge Base Subcommand Group

## Overview

This plan implements a dedicated `kb` subcommand group for the `okf-schema` CLI,
plus a standalone `okfkb` alias, to manage OKF bundles of the specialised
"knowledge base" type. The feature ships two primary commands (`okfkb init` and
`okfkb install`), extends the existing `okf-schema init` with a `--pattern kb`
flag, and bundles skills/guidelines as package data loaded via
`importlib.resources`.

## Architecture

### New Subpackage

```
src/okf_schema/kb/
├── __init__.py      # Package marker, re-exports
├── cli.py           # Click command group (init, install)
├── scaffold.py      # KB scaffold logic (dirs, schemas, index.md, log.md)
├── install.py       # Skill/guideline deployment + AGENTS.md patching
└── patterns.py      # INIT_PATTERNS registry dict
```

### Bundled Data

```
src/okf_schema/data/kb/
├── __init__.py      # Empty, required for importlib.resources
├── _schema/
│   ├── Base.schema.yaml
│   ├── Concept.schema.yaml
│   ├── Experiment.schema.yaml
│   ├── Finding.schema.yaml
│   ├── Playbook.schema.yaml
│   ├── Principle.schema.yaml
│   ├── Reference.schema.yaml
│   └── Structure.schema.yaml
├── skills/
│   ├── consolidate-knowledge-base/
│   │   └── SKILL.md
│   └── record-finding/
│       └── SKILL.md
└── guidelines/
    └── knowledge-base.guidelines.md
```

### CLI Integration Points

- `src/okf_schema/cli.py`: register `kb` group via `cli.add_command(kb)`
- `src/okf_schema/cli.py`: add `--pattern` option to existing `init` command
- `pyproject.toml`: add `okfkb` console_scripts entry point
- `pyproject.toml`: ensure `tool.hatch.build.targets.wheel.include` covers data files

## Implementation Steps

### Phase 1 — Bundled Assets and Package Data

1. **Create `src/okf_schema/data/kb/` structure**
   - Copy all 8 schema YAML files from `copilot-session-usage/knowledge/_schema/`
   - Copy `record-finding/SKILL.md` and `consolidate-knowledge-base/SKILL.md`
   - Copy `knowledge-base.guidelines.md`
   - Add empty `__init__.py` to make it a valid package

2. **Update `pyproject.toml`**
   - Add `okfkb = "okf_schema.kb.cli:kb"` to `[project.scripts]`
   - Verify `tool.hatch.build.targets.wheel.include` covers `src/okf_schema/data/`

3. **Verify bundled assets are loadable**
   - Write a quick smoke test using `importlib.resources.files("okf_schema.data.kb")`
   - Ensure all 8 schemas + 2 skills + 1 guideline are accessible

### Phase 2 — `kb` Subpackage Core Logic

4. **Create `src/okf_schema/kb/scaffold.py`**
   - `scaffold_kb(path: Path, force: bool = False) -> None`
   - Creates 8 content directories, copies 8 schemas from bundled data
   - Writes `index.md` and `log.md` with minimal OKF frontmatter
   - Errors if path exists and is non-empty (unless `--force`)
   - Prints confirmation summary

5. **Create `src/okf_schema/kb/install.py`**
   - `install_kb(target: Path, force: bool = False) -> None`
   - Detects `.agents/` or `.github/` in target; prefers `.agents/`
   - Copies skills to `<base>/skills/` and guideline to `<base>/guidelines/`
   - Skips existing files with warning; `--force` overwrites
   - Patches or creates `AGENTS.md` with guideline reference (idempotent)
   - Prints summary of installed/skipped files

6. **Create `src/okf_schema/kb/patterns.py`**
   - `INIT_PATTERNS: dict[str, Callable[[Path, bool], None]]`
   - Maps pattern names to scaffold functions
   - `register_pattern(name: str, fn: Callable[[Path, bool], None]) -> None`
   - `list_patterns() -> list[str]`

7. **Create `src/okf_schema/kb/cli.py`**
   - Click group `kb` with `init` and `install` subcommands
   - `init`: optional `PATH` arg, `--force` flag, delegates to `scaffold_kb`
   - `install`: optional `PATH` arg, `--force` flag, delegates to `install_kb`
   - Both print confirmation summaries

### Phase 3 — CLI Integration and `--pattern kb`

8. **Register `kb` group on top-level CLI**
   - Import `kb` group in `src/okf_schema/cli.py`
   - Add `cli.add_command(kb)` after existing commands
   - Verify `okf-schema kb --help` lists `init` and `install`

9. **Add `--pattern` flag to existing `init` command**
   - Add `@click.option("--pattern", default=None)` to `init`
   - When `--pattern` is provided, look up in `INIT_PATTERNS` registry
   - Delegate to registered scaffold function; pass `name` as `PATH`
   - Unknown pattern: error with list of available patterns
   - No `--pattern`: preserve existing behaviour exactly

10. **Add `okfkb` entry point**
    - Already configured in `pyproject.toml` from Phase 1
    - Verify `okfkb --help` produces identical output to `okf-schema kb --help`

### Phase 4 — Tests, Documentation, and Quality Gate

11. **Unit tests for scaffold and init**
    - `test_scaffold_kb_creates_all_dirs_and_files`
    - `test_scaffold_kb_errors_on_nonempty_dir`
    - `test_scaffold_kb_force_overwrites`
    - `test_scaffold_kb_schemas_are_valid_yaml`
    - `test_okfkb_init_cli_invokes_scaffold`
    - `test_okf_schema_init_pattern_kb_delegates`
    - `test_init_unknown_pattern_errors`

12. **Unit tests for install and patterns**
    - `test_install_kb_creates_agents_md`
    - `test_install_kb_skips_existing_files`
    - `test_install_kb_force_overwrites`
    - `test_install_kb_idempotent_agents_md`
    - `test_install_kb_prefers_dot_agents`
    - `test_install_kb_creates_dot_agents_when_neither_exists`
    - `test_patterns_registry_register_and_list`

13. **Integration tests, docs, and coverage**
    - End-to-end: `okfkb init` → `okfkb install` → verify structure
    - Verify `pip install` wheel contains bundled assets
    - Update `README.md` with Knowledge Base section
    - Create `docs/source/kb-commands.rst`
    - Run `just preflight` and verify ≥ 96% coverage

## Testing Strategy

- **TDD (red-green) for all coding tasks**: write failing test first, then
  implement.
- **Real temp dirs** (`tmp_path` fixture) for scaffold tests — actual filesystem
  operations.
- **Mock `shutil`** for install unit tests where appropriate, but also real
  temp-dir integration tests.
- **CliRunner** from `click.testing` for all CLI-level tests.
- **Coverage target**: 96% (project-wide threshold in `pyproject.toml`).
- **Type safety**: mypy strict mode must pass with no new errors.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **96% coverage bar** | Every new function has unit tests; integration tests cover CLI paths. Use `pytest --cov=okf_schema` locally before commit. |
| **importlib.resources packaging** | Smoke test verifies files are accessible from installed wheel. Hatchling `include` directive must cover `data/kb/`. |
| **AGENTS.md patching idempotency** | Check for existing reference line before appending; unit test verifies no duplication on second run. |
| **Backward compatibility of `init`** | `--pattern` defaults to `None`; existing code path is unchanged. Dedicated test asserts old behaviour. |
| **mypy strict mode** | All new functions fully typed; run `just typecheck` in every task. |

## Requirements Impact

No requirement traceability applicable to this change.

## Implementation Effort Estimation

| Metric | Fast (no inspector preflight) | Safe (inspector + preflight) |
|--------|-------------------------------|------------------------------|
| Tasks  | ~13                           | ~13                          |
| GU cost | ~13 GU                        | ~19.5 GU                     |
| Est. time  | ~65 min (5 min/GU)         | ~97 min                      |
| Est. tokens | ~13×avg_tokens            | ~19.5×avg_tokens             |

_Based on 0 historical gate runs. avg_gate_duration_min: null._

# Task 04 — Create scaffold.py with scaffold_kb() Function

**Phase**: Phase 2 — kb Subpackage Core Logic
**Depends on**: 01, 02, 03

## Objective

Implement `src/okf_schema/kb/scaffold.py` containing the `scaffold_kb()` function
that creates the canonical KB folder layout: 8 content directories, 8 schema files
(copied from bundled data), `index.md`, and `log.md`.

## Files to Modify/Create

- Create `src/okf_schema/kb/__init__.py` (package marker, can re-export)
- Create `src/okf_schema/kb/scaffold.py`
- Create `tests/test_kb_scaffold.py`

## Acceptance Criteria

- [ ] `scaffold_kb(path: Path, force: bool = False) -> None` exists and is fully typed
- [ ] Creates 8 directories: `concepts/`, `experiments/`, `findings/`, `guides/`, `ideas/`, `principles/`, `reference/`, `structures/`
- [ ] Creates `_schema/` with all 8 schema YAML files copied from bundled data
- [ ] Creates `index.md` with minimal OKF frontmatter (`okf_version: "0.1"`)
- [ ] Creates `log.md` with a date heading
- [ ] Errors with clear message if `path` exists and is non-empty (unless `force=True`)
- [ ] When `force=True`, overwrites existing files
- [ ] Prints a confirmation summary of what was created
- [ ] All code paths covered by tests (≥96% coverage contribution)
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100; Google docstrings |
| `pyproject.toml` | mypy strict: `disallow_untyped_defs=true` |
| `AGENTS.md` | TDD: write failing test first, then implement |
| `AGENTS.md` | Quality gate: `just preflight` |
| `03-specification.md` | `importlib.resources.files("okf_schema.data.kb")` is the required API |
| `03-specification.md` | If `PATH` already exists and is non-empty, error unless `--force` |

## Detailed Steps

1. **Red**: Write failing tests in `tests/test_kb_scaffold.py`:
   - `test_scaffold_kb_creates_all_dirs_and_files`
   - `test_scaffold_kb_errors_on_nonempty_dir`
   - `test_scaffold_kb_force_overwrites`
   - `test_scaffold_kb_schemas_are_valid_yaml`
   - `test_scaffold_kb_index_has_frontmatter`
   - `test_scaffold_kb_log_has_date_heading`

2. **Green**: Implement `src/okf_schema/kb/scaffold.py`:
   ```python
   from __future__ import annotations

   import datetime
   from pathlib import Path
   from typing import Any

   from importlib.resources import files

   import click


   def scaffold_kb(path: Path, force: bool = False) -> None:
       """Scaffold a knowledge-base bundle at *path*.

       Creates the canonical KB folder layout with 8 content directories,
       8 schema YAML files, index.md, and log.md.

       Args:
           path: Target directory for the KB bundle.
           force: If True, overwrite existing files.
       """
   ```

3. Use `files("okf_schema.data.kb")` to locate bundled assets. Copy schema files
   using `shutil.copyfile` or `pathlib.Path.write_bytes`.

4. Write `index.md` with:
   ```markdown
   ---
   okf_version: "0.1"
   links: []
   backlinks: []
   ---

   # knowledge
   ```

5. Write `log.md` with:
   ```markdown
   # Update Log

   ## {today}
   ```

6. Run tests: `uv run pytest tests/test_kb_scaffold.py -v`

7. Run `just preflight`.

8. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 04 --status done
   ```

## Testing Strategy

- Use `tmp_path` fixture for real filesystem operations.
- Test the error case by creating a file in the target dir before calling.
- Test `force=True` by pre-creating the dir and verifying overwrite.
- Verify schema files are valid YAML using `yaml.safe_load`.

## Notes

- The `index.md` and `log.md` content should be minimal but valid OKF.
- The schema files are copied as binary to preserve exact content.
- Consider using `shutil.copytree` for the `_schema/` directory if convenient.

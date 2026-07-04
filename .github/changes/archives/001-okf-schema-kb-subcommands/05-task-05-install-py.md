# Task 05 — Create install.py with install_kb() Function

**Phase**: Phase 2 — kb Subpackage Core Logic
**Depends on**: 01, 02, 03

## Objective

Implement `src/okf_schema/kb/install.py` containing the `install_kb()` function
that deploys bundled skills and guidelines into a target project, with conflict
resolution and AGENTS.md patching.

## Files to Modify/Create

- Create `src/okf_schema/kb/install.py`
- Create `tests/test_kb_install.py`

## Acceptance Criteria

- [ ] `install_kb(target: Path, force: bool = False) -> None` exists and is fully typed
- [ ] Detects `.agents/` or `.github/` in target; prefers `.agents/`; creates `.agents/` if neither exists
- [ ] Copies skills to `<base>/skills/` and guideline to `<base>/guidelines/`
- [ ] Skips existing files with warning; `--force` overwrites
- [ ] If `AGENTS.md` exists: appends guideline reference idempotently (no duplication)
- [ ] If `AGENTS.md` does not exist: creates minimal one with guideline reference and project stub
- [ ] Errors with clear message if `target` does not exist
- [ ] Prints a summary of installed / skipped files
- [ ] All code paths covered by tests
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100; Google docstrings |
| `pyproject.toml` | mypy strict: `disallow_untyped_defs=true` |
| `AGENTS.md` | TDD: write failing test first, then implement |
| `AGENTS.md` | Quality gate: `just preflight` |
| `03-specification.md` | Conflict resolution: skip existing files, warn; `--force` to overwrite |
| `03-specification.md` | AGENTS.md patching is idempotent |

## Detailed Steps

1. **Red**: Write failing tests in `tests/test_kb_install.py`:
   - `test_install_kb_creates_agents_md`
   - `test_install_kb_skips_existing_files`
   - `test_install_kb_force_overwrites`
   - `test_install_kb_idempotent_agents_md`
   - `test_install_kb_prefers_dot_agents`
   - `test_install_kb_creates_dot_agents_when_neither_exists`
   - `test_install_kb_errors_when_target_missing`

2. **Green**: Implement `src/okf_schema/kb/install.py`:
   ```python
   from __future__ import annotations

   from pathlib import Path
   from typing import Any

   from importlib.resources import files

   import click


   def install_kb(target: Path, force: bool = False) -> None:
       """Install KB skills and guidelines into *target* project.

       Args:
           target: Root directory of the target project.
           force: If True, overwrite existing files.
       """
   ```

3. Implement base-dir detection logic:
   ```python
   agents_dir = target / ".agents"
   github_dir = target / ".github"
   if agents_dir.exists():
       base = agents_dir
   elif github_dir.exists():
       base = github_dir
   else:
       base = agents_dir
       base.mkdir(parents=True)
   ```

4. Implement file copying with conflict resolution:
   - For each skill directory and the guideline file:
     - If destination exists and `not force`: skip and warn
     - Else: copy (using `shutil.copytree` for dirs, `shutil.copy2` for files)

5. Implement AGENTS.md patching:
   ```python
   agents_md = target / "AGENTS.md"
   guideline_ref = "- [Knowledge Base Guidelines](.agents/guidelines/knowledge-base.guidelines.md)"
   if agents_md.exists():
       content = agents_md.read_text(encoding="utf-8")
       if guideline_ref not in content:
           agents_md.write_text(content + "\n" + guideline_ref + "\n", encoding="utf-8")
   else:
       agents_md.write_text(
           "# AGENTS.md\n\n" + guideline_ref + "\n",
           encoding="utf-8",
       )
   ```
   (Adjust the reference path based on whether `.agents/` or `.github/` was used.)

6. Run tests: `uv run pytest tests/test_kb_install.py -v`

7. Run `just preflight`.

8. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 05 --status done
   ```

## Testing Strategy

- Use `tmp_path` to create simulated target projects.
- Mock `importlib.resources` or use a test helper that points to a temp data dir.
- Test idempotency by calling `install_kb` twice and asserting no duplicate lines.
- Test `.github/` fallback by creating only `.github/` in the target.

## Notes

- The AGENTS.md reference line should use a relative path that matches the actual
  install location (`.agents/guidelines/...` or `.github/guidelines/...`).
- Skills are directories — use `shutil.copytree` with `dirs_exist_ok=force`.
- Keep the summary output concise but informative.

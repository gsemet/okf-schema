# Task 11 — Unit Tests for install_kb and End-to-End Integration

**Phase**: Phase 4 — Tests, Documentation, and Quality Gate
**Depends on**: 05, 07

## Objective

Write comprehensive unit and integration tests for `install_kb`, the `kb install`
CLI command, and the `okfkb` entry point alias. Ensure all edge cases are covered.

## Files to Modify/Create

- Create `tests/test_kb_install.py` (if not created in Task 05)
- Create `tests/test_kb_cli.py` (if not created in Task 07)
- Modify `tests/test_integration.py` (add kb workflow test)

## Acceptance Criteria

- [ ] `test_install_kb_creates_agents_md` — creates minimal AGENTS.md with guideline reference
- [ ] `test_install_kb_skips_existing_files` — skips existing skills/guidelines with warning
- [ ] `test_install_kb_force_overwrites` — `--force` overwrites existing files
- [ ] `test_install_kb_idempotent_agents_md` — second run does not duplicate reference
- [ ] `test_install_kb_prefers_dot_agents` — uses `.agents/` when both exist
- [ ] `test_install_kb_creates_dot_agents_when_neither_exists` — creates `.agents/` if missing
- [ ] `test_install_kb_errors_when_target_missing` — errors if target path does not exist
- [ ] `test_kb_install_cli_invokes_install` — CLI test for `okf-schema kb install`
- [ ] `test_okfkb_alias_works` — verifies `okfkb` entry point resolves
- [ ] `test_end_to_end_init_then_install` — full workflow: init → install → verify
- [ ] All tests pass; coverage for new modules ≥ 96%
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100 |
| `pyproject.toml` | pytest with `--cov=okf_schema` |
| `AGENTS.md` | TDD: tests written before or alongside implementation |
| `AGENTS.md` | Use `CliRunner` for CLI tests |
| `03-specification.md` | `okfkb install [PATH]` copies skills and guideline, patches AGENTS.md |

## Detailed Steps

1. Ensure `tests/test_kb_install.py` exists with tests for `install_kb`:
   ```python
   from pathlib import Path
   from click.testing import CliRunner
   from okf_schema.kb.install import install_kb
   from okf_schema.cli import cli

   class TestInstallKb:
       def test_creates_agents_md(self, tmp_path: Path) -> None:
           target = tmp_path / "project"
           target.mkdir()
           install_kb(target)
           assert (target / "AGENTS.md").exists()
           text = (target / "AGENTS.md").read_text()
           assert "knowledge-base.guidelines.md" in text

       def test_skips_existing_files(self, tmp_path: Path) -> None:
           target = tmp_path / "project"
           target.mkdir()
           agents = target / ".agents"
           agents.mkdir()
           skills = agents / "skills" / "record-finding"
           skills.mkdir(parents=True)
           (skills / "SKILL.md").write_text("old")
           install_kb(target)
           assert (skills / "SKILL.md").read_text() == "old"

       def test_force_overwrites(self, tmp_path: Path) -> None:
           target = tmp_path / "project"
           target.mkdir()
           agents = target / ".agents"
           agents.mkdir()
           skills = agents / "skills" / "record-finding"
           skills.mkdir(parents=True)
           (skills / "SKILL.md").write_text("old")
           install_kb(target, force=True)
           assert (skills / "SKILL.md").read_text() != "old"

       def test_idempotent_agents_md(self, tmp_path: Path) -> None:
           target = tmp_path / "project"
           target.mkdir()
           install_kb(target)
           install_kb(target)
           text = (target / "AGENTS.md").read_text()
           assert text.count("knowledge-base.guidelines.md") == 1

       def test_prefers_dot_agents(self, tmp_path: Path) -> None:
           target = tmp_path / "project"
           target.mkdir()
           (target / ".agents").mkdir()
           (target / ".github").mkdir()
           install_kb(target)
           assert (target / ".agents" / "guidelines" / "knowledge-base.guidelines.md").exists()

       def test_creates_dot_agents_when_neither_exists(self, tmp_path: Path) -> None:
           target = tmp_path / "project"
           target.mkdir()
           install_kb(target)
           assert (target / ".agents").is_dir()
           assert (target / ".agents" / "skills").is_dir()

       def test_errors_when_target_missing(self, tmp_path: Path) -> None:
           target = tmp_path / "nonexistent"
           with pytest.raises(Exception):
               install_kb(target)
   ```

2. Ensure `tests/test_kb_cli.py` exists with CLI tests for `kb install`.

3. Add end-to-end test to `tests/test_integration.py`:
   ```python
   def test_kb_init_then_install(self, tmp_path: Path) -> None:
       """Full KB workflow: init a KB, then install skills into a project."""
       runner = CliRunner()
       kb_path = tmp_path / "mykb"
       project_path = tmp_path / "project"
       project_path.mkdir()

       # init
       result = runner.invoke(cli, ["kb", "init", str(kb_path)])
       assert result.exit_code == 0
       assert (kb_path / "concepts").is_dir()

       # install
       result = runner.invoke(cli, ["kb", "install", str(project_path)])
       assert result.exit_code == 0
       assert (project_path / ".agents" / "skills" / "record-finding" / "SKILL.md").exists()
       assert (project_path / "AGENTS.md").exists()
   ```

4. Run tests with coverage:
   ```bash
   uv run pytest tests/test_kb_install.py tests/test_kb_cli.py tests/test_integration.py -v --cov=okf_schema.kb --cov-report=term-missing
   ```

5. Run `just preflight`.

6. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 11 --status done
   ```

## Testing Strategy

- Use `tmp_path` for filesystem tests.
- Use `CliRunner` for CLI tests.
- Test idempotency by calling `install_kb` twice on the same target.
- Test `.github/` fallback by creating only `.github/` in the target.

## Notes

- The `okfkb` alias test may need to invoke the `kb` group directly since
  `CliRunner` tests the Python API, not the console script entry point.
- For the entry point test, you can verify `okfkb` is importable:
  ```python
  from okf_schema.kb.cli import kb
  assert kb is not None
  ```

# Task 10 — Unit Tests for scaffold_kb, init, and patterns

**Phase**: Phase 4 — Tests, Documentation, and Quality Gate
**Depends on**: 04, 06, 09

## Objective

Write comprehensive unit tests for `scaffold_kb`, the `init` command with
`--pattern`, and the `INIT_PATTERNS` registry. Ensure all edge cases and error
paths are covered to maintain the 96% coverage threshold.

## Files to Modify/Create

- Create `tests/test_kb_scaffold.py` (if not created in Task 04)
- Create `tests/test_kb_patterns.py` (if not created in Task 06)
- Modify `tests/test_cli_core.py` (add pattern-related tests)

## Acceptance Criteria

- [ ] `test_scaffold_kb_creates_all_dirs_and_files` — verifies 8 dirs + _schema + index.md + log.md
- [ ] `test_scaffold_kb_errors_on_nonempty_dir` — verifies error on existing non-empty dir
- [ ] `test_scaffold_kb_force_overwrites` — verifies `--force` overwrites existing files
- [ ] `test_scaffold_kb_schemas_are_valid_yaml` — parses all 8 schemas with `yaml.safe_load`
- [ ] `test_scaffold_kb_index_has_frontmatter` — verifies `okf_version` in index.md
- [ ] `test_scaffold_kb_log_has_date_heading` — verifies date heading in log.md
- [ ] `test_init_pattern_kb_delegates` — CLI test for `--pattern kb`
- [ ] `test_init_unknown_pattern_errors` — CLI test for unknown pattern
- [ ] `test_init_without_pattern_is_unchanged` — backward compatibility test
- [ ] `test_patterns_registry_register_and_list` — registry unit tests
- [ ] `test_patterns_register_duplicate_raises` — duplicate registration test
- [ ] All tests pass; coverage for new modules ≥ 96%
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100 |
| `pyproject.toml` | pytest with `--cov=okf_schema` |
| `AGENTS.md` | TDD: tests written before or alongside implementation |
| `AGENTS.md` | Use `CliRunner` for CLI tests |
| `03-specification.md` | All new code must maintain 96% coverage |

## Detailed Steps

1. Ensure `tests/test_kb_scaffold.py` exists with tests for `scaffold_kb`:
   ```python
   from pathlib import Path
   import yaml
   from click.testing import CliRunner
   from okf_schema.kb.scaffold import scaffold_kb
   from okf_schema.cli import cli

   class TestScaffoldKb:
       def test_creates_all_dirs_and_files(self, tmp_path: Path) -> None:
           target = tmp_path / "kb"
           scaffold_kb(target)
           dirs = ["concepts", "experiments", "findings", "guides",
                   "ideas", "principles", "reference", "structures"]
           for d in dirs:
               assert (target / d).is_dir()
           assert (target / "_schema" / "Base.schema.yaml").exists()
           assert (target / "index.md").exists()
           assert (target / "log.md").exists()

       def test_errors_on_nonempty_dir(self, tmp_path: Path) -> None:
           target = tmp_path / "kb"
           target.mkdir()
           (target / "existing.txt").write_text("hello")
           with pytest.raises(Exception):  # adjust to actual exception type
               scaffold_kb(target)

       def test_force_overwrites(self, tmp_path: Path) -> None:
           target = tmp_path / "kb"
           target.mkdir()
           (target / "index.md").write_text("old")
           scaffold_kb(target, force=True)
           assert "okf_version" in (target / "index.md").read_text()

       def test_schemas_are_valid_yaml(self, tmp_path: Path) -> None:
           target = tmp_path / "kb"
           scaffold_kb(target)
           schema_dir = target / "_schema"
           for schema_file in schema_dir.glob("*.yaml"):
               content = schema_file.read_text()
               yaml.safe_load(content)  # should not raise

       def test_index_has_frontmatter(self, tmp_path: Path) -> None:
           target = tmp_path / "kb"
           scaffold_kb(target)
           text = (target / "index.md").read_text()
           assert "okf_version" in text

       def test_log_has_date_heading(self, tmp_path: Path) -> None:
           target = tmp_path / "kb"
           scaffold_kb(target)
           text = (target / "log.md").read_text()
           assert text.startswith("# Update Log")
           import datetime
           today = datetime.date.today().isoformat()
           assert today in text
   ```

2. Ensure `tests/test_kb_patterns.py` exists with registry tests.

3. Add pattern CLI tests to `tests/test_cli_core.py`.

4. Run tests with coverage:
   ```bash
   uv run pytest tests/test_kb_scaffold.py tests/test_kb_patterns.py tests/test_cli_core.py -v --cov=okf_schema.kb --cov-report=term-missing
   ```

5. Run `just preflight`.

6. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 10 --status done
   ```

## Testing Strategy

- Use `tmp_path` for all filesystem tests.
- Use `CliRunner` for all CLI tests.
- Use `yaml.safe_load` to validate schema YAML validity.
- Test both happy paths and error paths.

## Notes

- If tests were already written in Tasks 04 and 06, this task is about ensuring
  completeness and coverage. Add any missing edge cases.
- The `scaffold_kb` function should raise a specific exception type for the
  non-empty directory case — document that type in the tests.

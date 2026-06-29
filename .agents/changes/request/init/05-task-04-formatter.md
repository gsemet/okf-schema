# Task 04: Frontmatter Formatter

**Depends on**: Task 02
**Estimated complexity**: High
**Type**: Feature
**Phase**: Phase 2 — Validation & Formatting Engine

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Implement the frontmatter formatter that flattens nested lists in YAML frontmatter while preserving comments and formatting via `ruamel.yaml`. Support in-place, `--check`, and `--diff` modes.

## Files to Modify/Create
- `src/okf_schema/formatter.py`
- `tests/test_formatter.py`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 04 --status in_progress --started-at now`
2. Create `src/okf_schema/formatter.py`:
   - `flatten_value(value)` — recursively flatten nested lists; pass through scalars and dicts
   - `format_frontmatter(text: str) -> str` — extract frontmatter, flatten all list values, re-serialize
   - `format_file(path: Path, check: bool = False, diff: bool = False) -> bool` — format a single file, return True if changed
   - `format_bundle(bundle: Path, check: bool = False, diff: bool = False) -> list[FormattedResult]` — format all concept files in bundle
   - `FormattedResult` dataclass: path, changed, diff (if diff mode)
3. Implement list flattening logic:
   - Walk the frontmatter dict values recursively
   - For any list value, flatten nested lists: `[[a, b], c] -> [a, b, c]`
   - Preserve dicts within lists (do not flatten dict values)
   - Do NOT modify non-list values
4. Ensure comment preservation:
   - Use `ruamel.yaml` round-trip mode
   - Comments attached to list items must be preserved
   - Blank lines and formatting should be maintained where possible
5. Write `tests/test_formatter.py`:
   - Test flattening of nested lists: `[[a, b], c] -> [a, b, c]`
   - Test preservation of comments in frontmatter
   - Test `check` mode: returns True when changes needed, False when already flat
   - Test `diff` mode: returns unified diff string
   - Test in-place mode: file is modified on disk
   - Test files without frontmatter are skipped
   - Test files with already-flat lists are not modified
6. Run `just preflight` and fix any issues
7. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 04 --status coded_not_reviewed --completed-at now`
8. Commit with a conventional commit message:
   `feat: implement frontmatter formatter with list flattening and diff mode`

## Acceptance Criteria
- [ ] Nested lists in frontmatter are flattened recursively
- [ ] Comments in YAML frontmatter are preserved after formatting
- [ ] `--check` mode returns True if changes needed, False otherwise; does not modify files
- [ ] `--diff` mode shows unified diff without modifying files
- [ ] Default mode modifies files in-place
- [ ] Files without frontmatter are skipped silently
- [ ] Already-flat files are not modified
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
Follow TDD and the red-green cycle on this task: write a failing test first, confirm it fails, then implement minimal code to make it pass.
- **Test file**: `tests/test_formatter.py`
- **Test cases**:
  - Flatten `tags: [[a, b], c]` to `tags: [a, b, c]`
  - Flatten deeply nested: `[[[a]], b]` to `[a, b]`
  - Preserve comments on list items and between keys
  - `check` mode detects needed changes, no file modification
  - `diff` mode returns non-empty diff for nested lists
  - In-place mode writes corrected content to file
  - Skip files without frontmatter
  - Idempotent: running formatter twice produces same result

## Notes
- `ruamel.yaml` round-trip is essential here. Use `YAML().load()` to get a `CommentedMap`, modify values, then `YAML().dump()` back to string.
- The flattening should only affect list values in the frontmatter dict, not the structure of the dict itself.
- Be careful with `ruamel.yaml` list representation — it may use inline `[a, b]` or block `- a\n- b` format. Preserve the original style when possible.

# Task 08: Integration Tests & Edge Cases

**Depends on**: Task 07
**Estimated complexity**: Medium
**Type**: Testing
**Phase**: Phase 4 — Tests, Docs, CI/CD & Skill

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Write comprehensive integration tests and edge-case coverage to reach 95% test coverage. Fill any gaps in the test suite.

## Files to Modify/Create
- `tests/test_integration.py`
- `tests/test_edge_cases.py`
- `tests/conftest.py` (pytest fixtures)
- Any missing test files for uncovered code paths

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 08 --status in_progress --started-at now`
2. Create `tests/conftest.py` with shared fixtures:
   - `valid_bundle(tmp_path)` — creates a complete valid OKF bundle
   - `invalid_bundle(tmp_path)` — creates a bundle with multiple errors
   - `empty_bundle(tmp_path)` — creates an empty bundle directory
   - `schema_db(tmp_path)` — creates a directory with test schema files
   - `nested_list_bundle(tmp_path)` — bundle with unflatten lists
3. Create `tests/test_integration.py`:
   - End-to-end: init → new → validate (pass) → format → index → search → graph → stats
   - Test that a full workflow produces expected outputs at each step
   - Test CLI pipeline: run multiple commands in sequence on same bundle
4. Create `tests/test_edge_cases.py`:
   - Empty bundle (no markdown files)
   - Bundle with only reserved files
   - Concept with empty frontmatter values
   - Concept with very long title/description
   - Concept with special characters in filenames
   - Schema DB directory that exists but is empty
   - Schema DB with invalid schema file
   - External links only (no broken links)
   - Circular links in graph
   - Unicode content in frontmatter and body
   - Bundle path that is a file, not a directory
   - Concept path with parent directory references
5. Run `pytest --cov=src/okf_schema --cov-report=term-missing` and identify uncovered lines
6. Add tests for any uncovered code paths
7. Ensure coverage is >= 95%
8. Run `just preflight` and fix any issues
9. Update `progress.json` via CLI:
    `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 08 --status coded_not_reviewed --completed-at now`
10. Commit with a conventional commit message:
    `test: add integration tests and edge case coverage`

## Acceptance Criteria
- [ ] `tests/conftest.py` provides reusable fixtures for all test types
- [ ] `tests/test_integration.py` covers end-to-end workflows
- [ ] `tests/test_edge_cases.py` covers at least 10 edge cases
- [ ] Code coverage is >= 95% across `src/okf_schema/`
- [ ] All uncovered lines are justified (e.g., `if TYPE_CHECKING:` blocks)
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
<!-- This task IS testing — no separate test file needed beyond the integration/edge case tests themselves. -->
- **Test files**: `tests/test_integration.py`, `tests/test_edge_cases.py`
- **Integration cases**:
  - Full workflow: init bundle, add concepts, validate, format, index, search, graph, stats
  - CLI sequence: multiple commands on same bundle produce consistent state
- **Edge cases**:
  - Empty bundle directory
  - Bundle with only index.md and log.md
  - Concept file with no frontmatter at all
  - Concept with `type: ""` (empty string)
  - Schema DB with malformed JSON schema
  - Markdown with only external links
  - Circular cross-references between concepts
  - Unicode characters in titles and tags
  - Very deeply nested list structures
  - File path that is not a directory passed as bundle

## Notes
- Use `tmp_path` pytest fixture for all filesystem operations to ensure isolation
- The `pytest-cov` report will show missing lines — target those specifically
- If coverage is below 95%, add tests rather than lowering the threshold
- Consider using `pytest-mock` for mocking file system edge cases

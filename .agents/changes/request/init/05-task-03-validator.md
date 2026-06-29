# Task 03: Bundle Validator Core

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

Implement the bundle validation engine with all error (E1-E6) and warning (W1-W6) rules, adapted from the reference `validate_okf.py` script.

## Files to Modify/Create
- `src/okf_schema/validator.py`
- `tests/test_validator.py`
- `tests/fixtures/bundle/` (test fixtures)
- `tests/fixtures/schema/` (test schema files)

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 03 --status in_progress --started-at now`
2. Create `src/okf_schema/validator.py` with these functions:
   - `load_schema_database(schema_db: Path) -> dict[str, dict]` — load `.schema.json` / `.schema.yaml` files into type→schema map
   - `validate_against_schema(frontmatter: dict, schema: dict, type_name: str) -> list[str]` — validate with `jsonschema.Draft202012Validator`
   - `validate_concept(path, report, bundle_root, schemas)` — E1, E2, E4, W1, W2, W3, W6
   - `validate_index(path, report, bundle_root)` — E3 (non-root index.md must NOT have frontmatter)
   - `validate_log(path, report)` — E3 (no frontmatter), W5 (ISO 8601 date headings)
   - `validate_bundle(bundle: Path, schemas: dict[str, dict] | None = None) -> Report` — orchestrates all validators, emits W4 (missing index.md)
   - **NEW** E5: Detect unflatten lists in frontmatter (nested list structures)
   - **NEW** E6: Detect reserved file naming conflicts (e.g., `index.md` in wrong location)
3. Create test fixtures:
   - `tests/fixtures/bundle/valid/` — a conformant OKF bundle with multiple concepts, index.md, log.md
   - `tests/fixtures/bundle/invalid/` — bundles triggering each E/W code individually
   - `tests/fixtures/schema/` — sample `.schema.json` and `.schema.yaml` files
4. Write `tests/test_validator.py`:
   - Test each error code E1-E6 with dedicated fixture
   - Test each warning code W1-W6 with dedicated fixture
   - Test `validate_bundle` with valid bundle (conformant, no warnings)
   - Test `validate_bundle` with empty bundle
   - Test `load_schema_database` with mixed JSON/YAML schemas
   - Test schema validation (E4) with matching and non-matching types
5. Run `just preflight` and fix any issues
6. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 03 --status coded_not_reviewed --completed-at now`
7. Commit with a conventional commit message:
   `feat: implement bundle validator with E1-E6 and W1-W6 rules`

## Acceptance Criteria
- [ ] All validation rules E1-E6 and W1-W6 are implemented
- [ ] `validate_bundle` returns a `Report` with correct `is_conformant` flag
- [ ] Each error/warning code has at least one dedicated test case
- [ ] Schema database loading supports both `.schema.json` and `.schema.yaml`
- [ ] E5 (unflatten list) detects nested lists in frontmatter
- [ ] E6 detects reserved file naming conflicts
- [ ] Tests cover edge cases: empty bundle, missing schema DB, external links
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
Follow TDD and the red-green cycle on this task: write a failing test first, confirm it fails, then implement minimal code to make it pass.
- **Test file**: `tests/test_validator.py`
- **Test cases**:
  - E1: file without frontmatter, file with unparseable YAML
  - E2: missing `type` field, empty `type` field
  - E3: non-root `index.md` with frontmatter, `log.md` with frontmatter
  - E4: frontmatter failing schema validation
  - E5: frontmatter with nested lists
  - E6: reserved file in unexpected location
  - W1: missing `title` or `description`
  - W2: broken internal markdown link
  - W3: missing `timestamp`
  - W4: directory without `index.md`
  - W5: `log.md` with non-ISO date headings
  - W6: type declared but no schema file found
  - Valid bundle: conformant with no errors or warnings
  - Empty bundle: valid but may have W4

## Notes
- The reference `validate_okf.py` has working implementations for most rules — refactor into clean functions, do not copy the argparse/print logic
- E5 (unflatten list) is a new rule not in the original script. A list is "unflatten" if it contains nested lists (e.g., `tags: [[a, b], c]`). The validator should detect any nested list structure in frontmatter values.
- E6 (reserved file naming conflict) flags when a file named `index.md` or `log.md` exists in a location where it shouldn't (e.g., not at directory level, or duplicate reserved files)

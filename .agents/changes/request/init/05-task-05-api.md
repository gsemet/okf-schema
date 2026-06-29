# Task 05: Public Python API

**Depends on**: Task 03, Task 04
**Estimated complexity**: Medium
**Type**: Feature
**Phase**: Phase 3 — Python API & CLI Wiring

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Create the public Python API (`api.py`) that exposes clean, typed functions for programmatic use of all okf-schema capabilities.

## Files to Modify/Create
- `src/okf_schema/api.py`
- `tests/test_api.py`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 05 --status in_progress --started-at now`
2. Create `src/okf_schema/api.py` with these public functions:
   - `validate_bundle(bundle_path: str | Path, schema_db: str | Path | None = None) -> Report` — validate a bundle, optionally with schema DB
   - `format_bundle(bundle_path: str | Path, check: bool = False, diff: bool = False) -> list[FormattedResult]` — format all concept files
   - `list_bundle(bundle_path: str | Path) -> list[ConceptSummary]` — list all concepts with path, type, title
   - `show_bundle(bundle_path: str | Path, concept_path: str) -> ConceptDetail` — show a single concept's frontmatter and body
   - `index_bundle(bundle_path: str | Path) -> list[IndexUpdate]` — regenerate all index.md files
   - `search_bundle(bundle_path: str | Path, query: str) -> list[SearchResult]` — search frontmatter fields
   - `graph_bundle(bundle_path: str | Path) -> dict[str, list[str]]` — concept link graph
   - `stats_bundle(bundle_path: str | Path) -> BundleStats` — bundle statistics
3. Define return types in `models.py` if not already present:
   - `ConceptSummary(path: str, type: str, title: str)`
   - `ConceptDetail(frontmatter: dict, body: str)`
   - `IndexUpdate(path: str, action: str)` — "created" or "updated"
   - `FormattedResult(path: str, changed: bool, diff: str | None)`
   - `BundleStats(...)` — all metrics from the stats spec
4. Implement `search_bundle`:
   - Case-insensitive substring match across `title`, `description`, `type`, `tags`
   - Return sorted results by path
5. Implement `graph_bundle`:
   - Parse all markdown links in concept bodies
   - Build adjacency dict: concept_path -> list of linked concept paths
   - Only include internal links to other concepts
6. Implement `stats_bundle`:
   - Count total files, concepts, files without frontmatter, total size
   - Count by type (for bar chart)
   - Count tags (for cloud bar chart)
   - Count total links and broken links
7. Implement `index_bundle`:
   - Adapt logic from `index_okf.py` reference script
   - For each directory containing markdown files, generate/update `index.md`
   - Preserve bundle-root frontmatter if present
   - Include child concepts and subdirectories with descriptions
8. Implement `list_bundle`:
   - Collect all non-reserved `.md` files
   - Extract type and title from frontmatter
   - Return sorted by path
9. Implement `show_bundle`:
   - Read concept file, extract frontmatter and body
   - Return structured data
10. Write `tests/test_api.py`:
    - Test each API function with fixture bundles
    - Test error handling: nonexistent bundle, invalid concept path
    - Test search with matching and non-matching queries
    - Test graph with cross-linked concepts
    - Test stats against known fixture metrics
11. Run `just preflight` and fix any issues
12. Update `progress.json` via CLI:
    `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 05 --status coded_not_reviewed --completed-at now`
13. Commit with a conventional commit message:
    `feat: add public Python API for bundle operations`

## Acceptance Criteria
- [ ] All 8 public API functions are implemented with type hints and docstrings
- [ ] `validate_bundle` delegates to validator.py and returns Report
- [ ] `search_bundle` performs case-insensitive substring search across frontmatter
- [ ] `graph_bundle` returns correct adjacency list for internal concept links
- [ ] `stats_bundle` computes all metrics matching the specification example
- [ ] `index_bundle` regenerates index.md files preserving root frontmatter
- [ ] `tests/test_api.py` covers all public functions with fixture bundles
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
Follow TDD and the red-green cycle on this task: write a failing test first, confirm it fails, then implement minimal code to make it pass.
- **Test file**: `tests/test_api.py`
- **Test cases**:
  - `validate_bundle` returns conformant Report for valid bundle
  - `validate_bundle` with schema_db loads and applies schemas
  - `format_bundle` returns list of FormattedResult
  - `list_bundle` returns sorted concepts with path/type/title
  - `show_bundle` returns frontmatter dict and body string
  - `index_bundle` creates missing index.md files
  - `search_bundle` finds concepts by title substring
  - `search_bundle` finds concepts by tag substring
  - `search_bundle` returns empty list for non-matching query
  - `graph_bundle` maps concept -> list of linked concepts
  - `stats_bundle` returns correct file counts and type distribution
  - Error: `validate_bundle` on nonexistent path raises appropriate exception

## Notes
- The API functions should accept both `str` and `Path` for path arguments
- Use `pathlib.Path` internally, resolve to absolute paths
- The `index_bundle` logic is adapted from `index_okf.py` — preserve descriptions from existing index.md entries when regenerating
- Stats bar charts should be simple ASCII bars using `█` and `▓` characters, scaled to a max width

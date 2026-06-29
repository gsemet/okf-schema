# Task 02: Internal Infrastructure & Built-in Schema

**Depends on**: Task 01
**Estimated complexity**: Medium
**Type**: Feature
**Phase**: Phase 1 — Package Scaffolding & Core Infrastructure

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Create the internal infrastructure layer: data models, YAML helpers, utilities, and the built-in minimal OKF schema. These are the building blocks for the validator and formatter.

## Files to Modify/Create
- `src/okf_schema/_internal/__init__.py`
- `src/okf_schema/_internal/models.py`
- `src/okf_schema/_internal/yaml.py`
- `src/okf_schema/_internal/utils.py`
- `src/okf_schema/schemas/__init__.py`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 02 --status in_progress --started-at now`
2. Create `src/okf_schema/_internal/models.py` with dataclasses:
   - `Finding(code: str, message: str, path: Path | None = None)`
   - `Report(errors: list[Finding], warnings: list[Finding])` with `is_conformant`, `add_error()`, `add_warning()`
   - `ConceptInfo(title: str, description: str, type: str)`
   - `SearchResult(path: str, type: str, title: str)`
   - `BundleStats(...)` — fields for all stats metrics
3. Create `src/okf_schema/_internal/yaml.py`:
   - `make_yaml() -> YAML` — configured `ruamel.yaml` instance with `preserve_quotes=True`, `default_flow_style=False`
   - `extract_frontmatter(text: str) -> tuple[str | None, str]` — parse `---` delimited frontmatter
   - `parse_yaml(yaml_text: str) -> dict | None` — parse with ruamel, return plain dict or None on failure
   - `dump_yaml(data: dict) -> str` — serialize dict to YAML string
4. Create `src/okf_schema/_internal/utils.py`:
   - `collect_markdown_files(bundle: Path) -> Iterable[Path]` — yield all `.md` files sorted
   - `resolve_link(target: str, source: Path, bundle_root: Path) -> Path | None` — resolve markdown links, return None for external
   - `find_broken_links(body: str, source: Path, bundle_root: Path) -> list[str]` — find broken internal links
   - `has_markdown_files(dir_path: Path) -> bool` — check if directory contains any `.md`
   - `get_concept_info(path: Path) -> ConceptInfo` — extract title/description/type from frontmatter
   - Constants: `RESERVED_FILES = {"index.md", "log.md"}`, `ISO8601_DATE_RE`, `MARKDOWN_LINK_RE`
5. Create `src/okf_schema/schemas/__init__.py`:
   - Define `MINIMAL_SCHEMA` as a JSON Schema dict requiring `type` (string, minLength 1)
   - Provide `get_builtin_schema() -> dict` function
6. Write unit tests in `tests/test_internal.py`:
   - Test `extract_frontmatter` with/without frontmatter, malformed delimiters
   - Test `parse_yaml` with valid/invalid YAML
   - Test `resolve_link` with relative, absolute, external links
   - Test `find_broken_links` with broken and valid links
   - Test `get_concept_info` with complete and missing frontmatter
7. Run `just preflight` and fix any issues
8. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 02 --status coded_not_reviewed --completed-at now`
9. Commit with a conventional commit message:
   `feat: add internal infrastructure models, yaml helpers, and built-in schema`

## Acceptance Criteria
- [ ] All internal modules are created with type hints and docstrings
- [ ] `tests/test_internal.py` covers all public functions in `_internal/`
- [ ] `ruamel.yaml` preserves quotes and comments in round-trip tests
- [ ] Link resolution correctly handles external URLs, relative paths, and absolute bundle-relative paths
- [ ] Built-in schema validates that `type` is a non-empty string
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
Follow TDD and the red-green cycle on this task: write a failing test first, confirm it fails, then implement minimal code to make it pass.
- **Test file**: `tests/test_internal.py`
- **Test cases**:
  - `extract_frontmatter` returns `(None, text)` when no frontmatter
  - `extract_frontmatter` parses valid `---` delimited frontmatter
  - `parse_yaml` returns dict for valid YAML, None for invalid
  - `resolve_link` returns None for `https://` and `mailto:` links
  - `resolve_link` resolves relative paths correctly
  - `find_broken_links` flags missing files, ignores external links
  - `get_concept_info` falls back to stem-based title when frontmatter missing
  - `make_yaml` round-trips comments and quotes

## Notes
- The reference scripts in `nestor-compendium/skills/Engineering/Knowledge_Graphs/okf/scripts/` contain working implementations of these helpers — adapt them, do not copy verbatim
- Ensure `ruamel.yaml` is configured to preserve comments for the formatter task later

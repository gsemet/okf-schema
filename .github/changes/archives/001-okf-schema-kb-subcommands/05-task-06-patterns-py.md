# Task 06 — Create patterns.py with INIT_PATTERNS Registry

**Phase**: Phase 2 — kb Subpackage Core Logic
**Depends on**: 04

## Objective

Implement `src/okf_schema/kb/patterns.py` containing the `INIT_PATTERNS` registry
dict and helper functions for extensible init pattern registration.

## Files to Modify/Create

- Create `src/okf_schema/kb/patterns.py`
- Create `tests/test_kb_patterns.py`

## Acceptance Criteria

- [ ] `INIT_PATTERNS: dict[str, Callable[[Path, bool], None]]` exists
- [ ] `register_pattern(name: str, fn: Callable[[Path, bool], None]) -> None` exists
- [ ] `list_patterns() -> list[str]` exists
- [ ] All functions fully typed
- [ ] Registering a duplicate name raises `ValueError`
- [ ] `list_patterns()` returns sorted list of registered names
- [ ] All code paths covered by tests
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100; Google docstrings |
| `pyproject.toml` | mypy strict: `disallow_untyped_defs=true` |
| `AGENTS.md` | TDD: write failing test first, then implement |
| `03-specification.md` | Pattern dispatch uses module-level registry dict |
| `03-specification.md` | Unknown pattern names produce clear error listing available patterns |

## Detailed Steps

1. **Red**: Write failing tests in `tests/test_kb_patterns.py`:
   - `test_init_patterns_is_dict`
   - `test_register_pattern_adds_to_registry`
   - `test_register_duplicate_raises_valueerror`
   - `test_list_patterns_returns_sorted_names`

2. **Green**: Implement `src/okf_schema/kb/patterns.py`:
   ```python
   from __future__ import annotations

   from pathlib import Path
   from typing import Callable

   INIT_PATTERNS: dict[str, Callable[[Path, bool], None]] = {}


   def register_pattern(name: str, fn: Callable[[Path, bool], None]) -> None:
       """Register an init pattern.

       Args:
           name: Pattern identifier (e.g., "kb").
           fn: Callable that accepts (path, force) and performs the scaffold.

       Raises:
           ValueError: If *name* is already registered.
       """
       if name in INIT_PATTERNS:
           raise ValueError(f"Pattern '{name}' is already registered.")
       INIT_PATTERNS[name] = fn


   def list_patterns() -> list[str]:
       """Return a sorted list of registered pattern names."""
       return sorted(INIT_PATTERNS.keys())
   ```

3. Run tests: `uv run pytest tests/test_kb_patterns.py -v`

4. Run `just preflight`.

5. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 06 --status done
   ```

## Testing Strategy

- Simple unit tests — no filesystem interaction needed.
- Use a dummy callable (e.g., `lambda path, force: None`) for registration tests.
- Verify `ValueError` is raised with the correct message on duplicate registration.

## Notes

- The registry is intentionally mutable at module level — patterns are registered
  at import time by subpackages.
- The `kb` pattern will be registered by importing `okf_schema.kb.scaffold` and
  calling `register_pattern("kb", scaffold_kb)` at the bottom of that module
  (or in `okf_schema/kb/__init__.py`).

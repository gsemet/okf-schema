# Read Before Implementing: Packaged Agent Skill Installation

## Change Summary

Implement the backlog change `install-skills-command`: ship seven complete agent
skills in the `okf-schema` wheel and expose family-scoped `install-skills`
commands from `okf-schema`, `okfkb`, and `okfreq`. The command contract replaces
the legacy `okfkb` installer and must work from an installed wheel.

## Start Here

Read these files before starting any task:

1. `01-request.md`
2. `02-interview-responses.md`
3. `03-specification.md`
4. `04-plan.md`
5. This file and the assigned `05-task-NN-*.md`

## Key Files and Modules

- `pyproject.toml` - Hatch build and console entry points
- `skills/` - canonical source skill trees
- `src/okf_schema/data/` - package resources
- `src/okf_schema/okfkb/install.py` - legacy installer being replaced
- `src/okf_schema/cli.py` - `okf-schema` Click group
- `src/okf_schema/okfkb/cli.py` - `okfkb` Click group
- `src/okf_schema/okfreq/cli.py` - `okfreq` Click group
- `tests/test_kb_install.py`, `tests/test_kb_cli.py`, and `tests/test_integration.py` - legacy expectations to migrate

## Project Rules & Guidelines

All tasks in this change MUST comply with the following project rules. Read
each applicable file before coding and keep it open during implementation.

| Rule file | What it enforces | Applies to |
|-----------|------------------|------------|
| `AGENTS.md` | Project architecture, tooling, navigation, and `just preflight` gate | Everything |
| `.github/guidelines/git-commit-message.guidelines.md` | Commit message conventions | Every commit |
| `.github/guidelines/python-unittest.guidelines.md` | pytest function tests, fixtures, parametrization, and test placement | Python tests and fixtures |
| `.github/guidelines/python-module-documentation.guidelines.md` | Typed public APIs, module/docstring conventions, and version directives | Maintained Python modules and CLI APIs |

> The Task Inspector **will verify compliance** with every applicable rule listed here.

## Commit Message Guideline

Source: `.github/guidelines/git-commit-message.guidelines.md`

The complete rules are reproduced verbatim:

1. Format the subject as `type(scope): description`; `scope` is optional. Use
   only `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `ci`,
   `chore`, `build`, or `revert`. Keep it at most 71 characters.
2. Apply limits to the final physical Git lines, not visual wrapping. Body
   lines must be at most 79 characters; 80 is invalid. Keep every trailer on
   one unwrapped, unindented line. Blank lines are exempt. Unbreakable URLs,
   hashes, and similar strings may exceed 79 characters only on their own
   line. A workflow may be stricter, never looser or conflicting.
3. Prefer `git commit -F <message-file>`. With `-m`, the first value is the
   subject and each later value is a paragraph separated by a blank line; use
   one value per paragraph, never per wrapped line.
4. Body text must describe user benefits, required user knowledge, or the
   resolved limitation. Do not describe refactoring, internal functions,
   changed files, methods, tests, or the number of checks run. Rewrite any diff
   summary so it says what users can now do or what limitation was fixed.
5. For breaking changes, put `!` in the subject and include a
   `BREAKING CHANGE:` section with explicit migration steps.
6. Do not add `Signed-off-by` unless a human requests it. Do not use
   `git commit -s` or add it implicitly. If requested, add and verify it
   deliberately. A human may use it to indicate ownership of AI-generated
   content.
7. If AI generated most of the message, append this body trailer:
   `Assisted-by: MODEL_PROVIDER:MODEL_NAME FRAMEWORK`. Use the underlying model
   family/vendor, never the interface or IDE; use the specific model version;
   and include the optional SDD framework only when it drove the
   implementation. Determine provider and model from current harness/session
   metadata. For Craftsman, use `Craftsman-Session-Main-Model` or its equivalent
   usage record. Never copy attribution or guess. If it cannot be verified,
   stop and obtain it.

For Craftsman workflow commits, do not hand-author session or PRD-scoping
trailers. The centralized amendment command owns exactly:
`Craftsman-Change-Request-Name`, `Craftsman-Session-ID`,
`Craftsman-Session-Main-Model`, `Craftsman-Session-Acc-Usage`, and
`Craftsman-Session-Acc-AIC`. Missing session context is warn-only, but the PRD
marker remains required to scope current history. Former session-trailer
vocabulary is not a compatibility alias.

## Preflight

Before marking any task complete, run the focused tests named in that task and
then run the complete quality gate:

```bash
just preflight
```

## Coding Principles

- **Think before coding**: State assumptions, identify the controlling path,
  and use a focused failing test to validate the intended behavior.
- **Simplicity first**: Prefer the smallest design that fully satisfies the
  specified contract; do not add speculative destination kinds or modes.
- **Surgical changes**: Preserve unrelated CLI and package behavior and avoid
  broad refactors beyond the superseded installer.
- **Goal-driven execution**: Keep every edit tied to an acceptance criterion,
  validate after each coherent change, and finish with the full quality gate.
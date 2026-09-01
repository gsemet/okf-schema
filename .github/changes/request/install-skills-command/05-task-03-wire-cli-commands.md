# Task 03: Wire Consistent CLI Commands

**Depends on**: Task 02
**Estimated complexity**: High
**Type**: Feature
**Phase**: Phase 2 - Command Integration and Delivery

## Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

- `AGENTS.md` - CLI architecture, project commands, and quality gate.
- `.github/guidelines/git-commit-message.guidelines.md` - every commit.
- `.github/guidelines/python-unittest.guidelines.md` - Click and integration tests.
- `.github/guidelines/python-module-documentation.guidelines.md` - changed public CLI commands and options.

## Objective

Expose the specified `install-skills` interface from all three console entry
points, with family isolation, consistent destination semantics, auditable
output, and nonzero failures.

## Files to Modify/Create

- `src/okf_schema/cli.py`
- `src/okf_schema/okfkb/cli.py`
- `src/okf_schema/okfreq/cli.py`
- `tests/test_cli_core.py`
- `tests/test_kb_cli.py`
- `tests/test_okfreq_cli.py`
- `tests/test_integration.py`

## Detailed Steps

1. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 03 --status in_progress --started-at now`.
2. Add failing Click tests for the optional `DESTINATION`, `--agent-copilot`,
   `--local-copilot`, and `--local-agents` interface on all three groups.
3. Add or reuse a small Click decorator/helper only if it keeps the three command
   contracts identical without obscuring each group's owned family.
4. Wire `okf-schema` to install only `okf-schema`, `okfkb` to install the base
   and every packaged `okfkb-*` skill, and `okfreq` to install the base and every
   packaged `okfreq-*` skill.
5. Print the resolved destination before per-skill results and map installer
   failures to a clear Click error/nonzero exit status.
6. Replace legacy `okfkb` tests and integration expectations: no `--force`, no
   guideline, no `AGENTS.md` mutation, no inferred agent root, no skip-on-exist.
7. Verify a supplied destination wins even when a selector is present, and that
   relative destinations/local selectors resolve from the command working directory.
8. Run `uv run -- pytest tests/test_cli_core.py tests/test_kb_cli.py tests/test_okfreq_cli.py tests/test_integration.py` and fix failures.
9. Run `just preflight` and fix all issues until it completes successfully.
10. If requirement traceability becomes applicable, run
    `craftsman req update-coverage`; otherwise do not create requirement changes.
11. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 03 --status coded_not_reviewed --completed-at now --coder-model "<model-name>" --summary "Exposed consistent family-scoped install-skills commands"`.
12. Commit using the discovered project convention, then let the Craftsman coder
    protocol apply centralized session and PRD trailers.

## Acceptance Criteria

- [ ] All three entry points expose the same positional destination and selector flags.
- [ ] No destination and no selector defaults to `~/.copilot/skills`.
- [ ] Explicit destinations take precedence and relative/local destinations resolve from the current working directory.
- [ ] Each command installs exactly its owned family and leaves other family directories untouched.
- [ ] Output includes the effective destination and one `installed` or `updated` result per owned skill.
- [ ] Staging, symlink, and replacement failures are clear and return nonzero.
- [ ] `okfkb install-skills` no longer exposes or performs any rejected legacy behavior.
- [ ] Focused tests and `just preflight` pass after all coding is complete.

## Testing Strategy

Follow TDD and the red-green cycle on this task: write a failing test first,
confirm it fails, then implement minimal code to make it pass.

- **Test files**: `tests/test_cli_core.py`, `tests/test_kb_cli.py`, `tests/test_okfreq_cli.py`
- **Test cases**: help/option parity; default destination; three selectors;
  absolute and relative explicit destinations; precedence; family isolation;
  installed/updated output; missing parent creation; symlink and staged-failure errors.
- **Test file**: `tests/test_integration.py`
- **Test cases**: update the existing KB workflow to the skills-only destination
  contract and assert removed side effects remain absent.

## Notes

Do not let the root `okf-schema --quiet` option silently redefine this command's
specified reporting unless the existing Click architecture requires a documented
global behavior. No command-specific `--quiet`, `--dry-run`, or `--force` belongs
in this change.
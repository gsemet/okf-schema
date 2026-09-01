## INSPECTOR FEEDBACK (Full History)

**Status**: Incomplete - Requires rework

### Round 1 — ❌ FAIL — 2026-09-02T00:56:42Z

INCOMPLETE. Review envelope: task 04, file
05-task-04-document-and-verify-distribution.md, PRD
install-skills-command, phase phase-2, Coder commit
3d849e5f743c7f80b951069eba0d6d640243b594, first review, canonical agent
Craftsman: Task Inspector Subagent, selected model unavailable.

Full pass: the three base skills contain both required `uv tool` commands,
name all three console entry points, distinguish CLI tool installation from
agent-skill folder installation, and their canonical and packaged copies are
recursively identical. The changed commit also adds coverage for the three
families and representative nested resources.

Blocking distribution-test defect: `tests/test_skill_resources.py:147-149`
sets `PYTHONPATH` to the host test environment's entire `site-packages`
directory while installing the wheel with `--no-deps` at lines 139-145. That
directory contains `_editable_impl_okf_schema.pth`, which resolves
`okf_schema` to the repository checkout's `src/okf_schema` when the subprocess
runs. A direct check using the test's exact environment resolves
`okf_schema.__file__` to `/Users/az02065/Projects/DevTools/okf-schema/src/okf_schema/__init__.py`.
The test therefore does not prove that the installed wheel supplies the
commands or nested resources without the source checkout on `PYTHONPATH`.
The acceptance criteria for all three commands in an isolated built-wheel
environment and readable installed nested content remain unverified.

Applicable guideline failure: the new repeated-input documentation test loops
over three skill roots at `tests/test_skill_resources.py:105-110`, while
`.github/guidelines/python-unittest.guidelines.md` requires
`@Parametrization` for multiple inputs exercising the same logic.

Quality gate warning: Coder session artifacts containing a completed final
`just preflight` invocation were not located, so preflight completion cannot
be verified under the session-log-only protocol. This warning does not by
itself determine the verdict.

Required rework: make the built-wheel subprocess genuinely independent of the
repository checkout and provide a valid isolated-environment assertion for
the three console scripts and nested resources; bring the repeated-input test
into compliance with the applicable parametrization guideline. Re-submit
after the focused distribution evidence and final quality gate are complete.

# Task 04: Document and Verify Installed Distribution

**Depends on**: Task 01, Task 03
**Estimated complexity**: Medium
**Type**: Documentation
**Phase**: Phase 2 - Command Integration and Delivery

## Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

- `AGENTS.md` - package commands and complete quality gate.
- `.github/guidelines/git-commit-message.guidelines.md` - every commit.
- `.github/guidelines/python-unittest.guidelines.md` - distribution regression tests.

## Objective

Teach users how CLI tool installation differs from agent-skill installation,
keep packaged base-skill documents synchronized, and verify the commands from a
built wheel rather than the source tree.

## Files to Modify/Create

- `skills/okf-schema/SKILL.md`
- `skills/okfkb/SKILL.md`
- `skills/okfreq/SKILL.md`
- `src/okf_schema/data/skills/okf-schema/SKILL.md`
- `src/okf_schema/data/skills/okfkb/SKILL.md`
- `src/okf_schema/data/skills/okfreq/SKILL.md`
- `tests/test_skill_resources.py`

## Detailed Steps

1. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 04 --status in_progress --started-at now`.
2. Add concise prerequisite sections to the three canonical base skills showing
   `uv tool install okf-schema` and `uv tool upgrade okf-schema`.
3. State that the tool installation exposes `okf-schema`, `okfkb`, and `okfreq`,
   then distinguish that operation from running each family's `install-skills`
   command to place agent folders.
4. Synchronize those three documents into package resources and keep the parity
   test from Task 01 passing.
5. Build a wheel, install it into an isolated environment, invoke all three
   console scripts, and inspect nested installed resource content without the
   repository package on `PYTHONPATH`.
6. Run `uv run -- pytest tests/test_skill_resources.py` and any focused CLI
   distribution test added by Task 03.
7. Run `just preflight` and fix all issues until it completes successfully.
8. If requirement traceability becomes applicable, run
   `craftsman req update-coverage`; otherwise do not create requirement changes.
9. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 04 --status coded_not_reviewed --completed-at now --coder-model "<model-name>" --summary "Documented and verified installed-wheel skill deployment"`.
10. Commit using the discovered project convention, then let the Craftsman coder
    protocol apply centralized session and PRD trailers.

## Acceptance Criteria

- [ ] Each base skill shows both required `uv tool` commands.
- [ ] Each base skill states that the tool exposes all three console entry points.
- [ ] Documentation clearly separates Python CLI installation from agent-skill folder installation.
- [ ] Canonical and packaged copies of all skill content remain recursively identical.
- [ ] All three commands successfully install complete owned families from an isolated built-wheel environment.
- [ ] Installed nested references/assets are readable without a source checkout.
- [ ] Focused tests and `just preflight` pass after all work is complete.

## Testing Strategy

Follow TDD and the red-green cycle for documentation parity and distribution
behavior: make the synchronization or installed-wheel assertion fail first,
then apply the smallest documentation/resource update.

- **Test file**: `tests/test_skill_resources.py`
- **Test cases**: exact canonical/package parity after documentation changes;
  built-wheel installation into an isolated environment; invocation of all
  console scripts; nested installed content available without source paths.

## Notes

Keep prerequisite text concise and operational. Do not expand this task into a
general README or documentation rewrite.

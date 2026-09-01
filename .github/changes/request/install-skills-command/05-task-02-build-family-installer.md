# INSPECTOR FEEDBACK (Full History)

**Status**: Incomplete - Requires rework

### Round 3 — ❌ FAIL — 2026-09-01T12:30:32.705693+00:00

**Review envelope**: Task `02`, file `05-task-02-build-family-installer.md`,
PRD `install-skills-command`, phase `phase-1`, Coder commit
`5901b756ac26cabd2f103efd9d4860cdae8e9685`, re-review attempt 2, canonical
agent `Craftsman: Task Inspector Subagent`, selected model unavailable in
active session metadata.

**Full pass**: Destination selectors and precedence, immutable family
ownership, family-wide staging before mutation, normal-directory replacement
and statuses, parent creation, unrelated-content preservation, owned skill
symlink rejection, legacy contract removal, requirement markers/frontmatter,
and requirements lint all pass.

**Blocking finding**: `resolve_destination()` follows an explicit or selector
destination symlink with `Path.resolve()` at
`src/okf_schema/skill_installer.py:114` and `:127`; the `okfkb` CLI then passes
that resolved target to `install_kb()` at `src/okf_schema/okfkb/cli.py:117-123`.
A minimal public-path check installed `okf-schema` through an explicit symlink,
proving that the installer mutates the link target instead of rejecting the
destination link. Add coverage for the public resolve-then-install path and
preserve the symlink so `install_skill_family()` can reject it.

**Delta pass against Round 2**:

- **Requirements traceability**: ✅ Resolved. The changed implementation and
  test files have requirement markers, and generated coverage lists them.
- **Retired installer contract**: ✅ Resolved. `install_kb()` has a strict
  destination-only signature, and the install command rejects `--force`.
- **Module documentation**: ✅ Resolved. Public installer APIs contain the
  required runnable `Examples` sections.
- **Quality gate evidence**: ⚠️ Still unverified. The Coder session log has no
  completed `just preflight` invocation; this remains a warning under the
  session-log-only protocol.

**OWASP review**: ❌ Destination symlink traversal is an input-validation and
least-privilege safety defect. No other security findings were identified.

**Next steps for Coder**:

1. Prevent destination normalization from following an explicit or selector
   symlink before the installer performs its rejection check.
2. Add a focused test covering the public resolve-then-install path and
   confirming that the symlink and its target remain unchanged.
3. Run the focused tests and provide session-log evidence of a completed
   `just preflight` invocation before resubmitting the task.

### Round 2 — ❌ FAIL — 2026-09-01

**Review envelope**: Task `02`, file `05-task-02-build-family-installer.md`,
PRD `install-skills-command`, phase `phase-1`, Coder commit
`7fb7b2747ab312aa3c0f28026f62bcbdf98ea5d9`, re-review attempt 1, canonical
agent `Craftsman: Task Inspector Subagent`, selected model
`Gemini 3.1 Pro (Preview) (copilot)`.

**Full pass**:

- ✅ Immutable family definitions match the specified command ownership.
- ✅ Complete-family staging occurs before destination creation or owned-path
   mutation, with injected preparation-failure coverage.
- ✅ New and updated installations report `installed` and `updated`, replace
   normal owned directories, remove stale owned files, and preserve unrelated
   content.
- ✅ Destination and owned symbolic links are rejected without following,
   unlinking, or replacing them.
- ✅ The retired `okfkb` guideline, `AGENTS.md`, inference, skip, and `--force`
   behavior is no longer reachable through the install command or facade.
- ❌ Requirement coverage was stale: the committed requirement frontmatter did
   not list the shared installer or focused installer tests.
- ❌ `tests/test_skill_installer.py` had no `@tests_req
   SwRS-OKFSCHEMA-OKFKB-002` marker.
- ⚠️ No Coder session artifact contained a completed `just preflight`
   invocation. The required quality gate remained unverified under the
   session-log-only protocol and was not re-executed during inspection.

**Delta pass against Round 1**:

- **Requirements traceability**: ❌ Not resolved. The focused installer test
  was unmarked and generated coverage was not updated for the changed files.
- **Retired installer contract**: ✅ Resolved. `install_kb()` no longer accepts
  arbitrary legacy options, and the install command rejects `--force`.
- **Module documentation**: ✅ Resolved. `resolve_destination()` and
  `install_skill_family()` contain runnable `Examples` sections.

**OWASP review**: No security findings identified in the changed
implementation or tests.

### Round 1 — ❌ FAIL — 2026-09-01T12:08:49.537685+00:00

**Review envelope**: Task `02`, phase `phase-1`, Coder commit
`43c050882f34ff881c51b3da9cd0e2412235171a`, first review, canonical agent
`Craftsman: Task Inspector Subagent`, selected model unavailable.

**Full pass**: Shared family staging, destination resolution,
normal-directory replacement, status reporting, unrelated-content preservation,
and pre-mutation symlink checks were present.

**Blocking findings**: Requirement scope identified
`SwRS-OKFSCHEMA-OKFKB-002`, but changed implementation files lacked
`@implements_req`, changed test files lacked `@tests_req`, and generated
coverage frontmatter was stale. The legacy `install_kb()` facade still accepted
arbitrary `_legacy_options`, while `src/okf_schema/okfkb/cli.py` still exposed
and forwarded `--force` and retained the old project-target behavior. Public
installer APIs with more than two parameters lacked runnable `Examples`
sections.

**Quality gate**: ⚠️ No Coder session artifact contained a completed
`just preflight` invocation, so the criterion was unverified under the
session-log-only protocol. Requirements lint passed with zero violations.

**OWASP review**: No security findings identified in the changed
implementation or tests.

# Task 02: Build the Staged Family Installer

**Depends on**: Task 01
**Estimated complexity**: High
**Type**: Feature
**Phase**: Phase 1 - Resource and Installer Foundation

## Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

- `AGENTS.md` - package architecture, project commands, and quality gate.
- `.github/guidelines/git-commit-message.guidelines.md` - every commit.
- `.github/guidelines/python-unittest.guidelines.md` - installer tests and fixtures.
- `.github/guidelines/python-module-documentation.guidelines.md` - typed installer API and error documentation.

## Objective

Provide one reusable installer that resolves destinations consistently, stages a
whole owned family before mutation, safely creates or updates owned skill
directories, and preserves unrelated destination content.

## Files to Modify/Create

- `src/okf_schema/skill_installer.py`
- `tests/test_skill_installer.py`
- `src/okf_schema/okfkb/install.py`
- `tests/test_kb_install.py`

## Detailed Steps

1. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 02 --status in_progress --started-at now`.
2. Write failing tests for explicit absolute/relative destinations, global and
   local selector resolution, missing parent creation, and explicit destination
   precedence.
3. Define immutable `okf-schema`, `okfkb`, and `okfreq` family membership and a
   typed result/error surface that command modules can consume.
4. Implement complete-family staging from `importlib.resources`; inject or
   isolate the staging boundary so tests can prove a preparation failure leaves
   all owned destination directories unchanged.
5. Implement new-directory installation and same-parent replacement of existing
   normal directories, reporting `installed` versus `updated` and preserving
   every unrelated directory/file.
6. Detect each owned path with `is_symlink()` before replacement and fail without
   following, unlinking, or replacing the symlink.
7. Remove or reduce the old knowledge-base installer so guideline copying,
   `AGENTS.md` patching, base-directory inference, skip behavior, and `force`
   semantics are no longer reachable from the new contract.
8. Run `uv run -- pytest tests/test_skill_installer.py tests/test_kb_install.py`
   and fix failures.
9. Run `just preflight` and fix all issues until it completes successfully.
10. If requirement traceability becomes applicable, run
    `craftsman req update-coverage`; otherwise do not create requirement changes.
11. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 02 --status coded_not_reviewed --completed-at now --coder-model "<model-name>" --summary "Implemented staged family-scoped skill installation"`.
12. Commit using the discovered project convention, then let the Craftsman coder
    protocol apply centralized session and PRD trailers.

## Acceptance Criteria

- [ ] Destination resolution implements the default, all selectors, relative paths, and explicit-path precedence.
- [ ] Each family contains exactly the skills owned by its invoking command.
- [ ] The complete family is staged before any owned destination path is mutated.
- [ ] Existing owned normal directories are replaced and reported as `updated`; new ones are `installed`.
- [ ] Missing destination parents are created while unrelated destination content remains unchanged.
- [ ] Any owned symbolic link causes a clear failure and is not followed, unlinked, or replaced.
- [ ] Legacy guideline, `AGENTS.md`, inference, skipping, and force behavior is removed from the installer surface.
- [ ] Focused tests and `just preflight` pass after all coding is complete.

## Testing Strategy

Follow TDD and the red-green cycle on this task: write a failing test first,
confirm it fails, then implement minimal code to make it pass.

- **Test file**: `tests/test_skill_installer.py`
- **Test cases**: family definitions; selector/path resolution; parent creation;
  installation/update statuses; stale file removal on replacement; unrelated
  content preservation; owned symlink rejection; injected staging failure with
  byte-for-byte unchanged owned directories.
- **Test file**: `tests/test_kb_install.py`
- **Test cases**: migrate or remove every assertion tied only to the retired
  knowledge-base-specific contract.

## Notes

Atomicity is required for each final directory replacement and staging must be
family-wide. A complex rollback after a rare failure during final replacement
is explicitly outside scope, but the error must remain clear and nonzero.

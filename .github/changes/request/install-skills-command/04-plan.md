# Implementation Plan: Packaged Agent Skill Installation

## Overview

Package the seven repository-owned skill trees below `okf_schema.data` and add a
shared installer that all three Click entry points invoke with an explicit skill
family. The installer will resolve the selected destination, stage an entire
family from `importlib.resources`, reject owned symlinks, and replace owned
normal directories without touching unrelated content.

## Architecture Changes

- Add a package-owned skill resource tree containing exact copies of the seven
  canonical skill directories, including nested references and assets.
- Replace the knowledge-base-specific installer with a reusable installation
  module responsible for destination resolution, resource staging, and safe
  directory replacement.
- Keep command ownership in each existing Click group: `okf-schema`, `okfkb`,
  and `okfreq` pass only their declared family to the shared installer.
- Remove the old installer's guideline deployment, `AGENTS.md` mutation,
  directory inference, skip behavior, and `--force` contract.

## Implementation Steps

### Step 1: Package all canonical skill resources

**Files to modify/create**:
- `src/okf_schema/data/skills/` - package-owned copies of all seven complete skill trees
- `src/okf_schema/data/skills/__init__.py` - resource package marker
- `pyproject.toml` - ensure skill resources are included in wheels and source distributions
- `tests/test_skill_resources.py` - verify packaged and built-wheel resource completeness

**Technical approach**:
Copy the canonical skill trees into the Python package without flattening nested
content. Add tests that enumerate the expected family roots through
`importlib.resources` and inspect a built wheel so success does not depend on a
source checkout.

**Dependencies**: None

### Step 2: Implement staged family installation

**Files to modify/create**:
- `src/okf_schema/skill_installer.py` - shared families, destination resolution, staging, and replacement
- `tests/test_skill_installer.py` - focused filesystem and failure-behavior tests
- `src/okf_schema/okfkb/install.py` - remove or reduce the superseded legacy installer surface
- `tests/test_kb_install.py` - remove or migrate tests for the retired contract

**Technical approach**:
Represent command ownership as explicit immutable family definitions. Resolve an
explicit destination before selectors, stage every family member into one
temporary area using `importlib.resources`, then mutate the destination only
after staging succeeds. Reject owned symlinks before replacement and use
same-parent temporary/backup paths plus filesystem renames to replace normal
directories while preserving unrelated entries.

**Dependencies**: Step 1

### Step 3: Expose one consistent command from every entry point

**Files to modify/create**:
- `src/okf_schema/cli.py` - add `okf-schema install-skills`
- `src/okf_schema/okfkb/cli.py` - migrate `okfkb install-skills`
- `src/okf_schema/okfreq/cli.py` - add `okfreq install-skills`
- `tests/test_cli_core.py` - core command contract tests
- `tests/test_kb_cli.py` - migrated knowledge-base command tests
- `tests/test_okfreq_cli.py` - requirements command tests
- `tests/test_integration.py` - update legacy workflow expectations

**Technical approach**:
Apply one reusable Click option/argument contract to each group while retaining
the groups' existing help conventions and exception handling. Each command
selects only its owned family, prints the resolved destination and per-skill
`installed` or `updated` result, and returns a nonzero status for staging,
symlink, or replacement errors.

**Dependencies**: Step 2

### Step 4: Document installation and verify distribution behavior

**Files to modify/create**:
- `skills/okf-schema/SKILL.md` - tool installation prerequisite and command distinction
- `skills/okfkb/SKILL.md` - tool installation prerequisite and family command
- `skills/okfreq/SKILL.md` - tool installation prerequisite and family command
- `src/okf_schema/data/skills/okf-schema/SKILL.md` - synchronize packaged base skill
- `src/okf_schema/data/skills/okfkb/SKILL.md` - synchronize packaged base skill
- `src/okf_schema/data/skills/okfreq/SKILL.md` - synchronize packaged base skill
- `tests/test_skill_resources.py` - assert canonical and packaged documentation stay aligned

**Technical approach**:
Add concise `uv tool install okf-schema` and `uv tool upgrade okf-schema`
prerequisites to the three base skills, explicitly distinguishing CLI tool
installation from agent-skill folder installation. Rebuild the distribution,
exercise installed-wheel commands in isolation, and run the complete project
quality gate.

**Dependencies**: Steps 1 and 3

## Testing Strategy

- **Unit tests**: Cover destination precedence, all selectors, relative-path
  resolution, family ownership, parent creation, status reporting, replacement,
  unrelated-content preservation, symlink rejection, and staging failure.
- **Integration tests**: Build and inspect the wheel, install it into an isolated
  environment, and invoke all three console entry points against temporary
  destinations.
- **Manual testing**: Review `--help` for each entry point and inspect one
  installed family to confirm nested references/assets and readable reporting.

## Risks and Mitigations

- **Resource trees drift from repository skills**: Packaged copies can become
  stale. -> **Mitigation**: Add a recursive canonical-versus-packaged parity test.
- **Partial family preparation mutates a destination**: A missing nested resource
  could leave an upgrade half-applied. -> **Mitigation**: Stage the complete
  family before creating or replacing owned destination directories.
- **Replacement crosses filesystem boundaries**: Temporary directories created
  elsewhere can make rename-based replacement non-atomic. -> **Mitigation**:
  create replacement paths under the destination parent.
- **Symlink handling escapes the target**: Generic removal can follow or replace
  an owned symlink. -> **Mitigation**: use `Path.is_symlink()` checks before all
  destination mutation and fail with the owned skill name.
- **Legacy behavior remains reachable**: Old tests or wrappers may preserve
  guideline/`AGENTS.md`/`--force` behavior. -> **Mitigation**: add explicit
  negative CLI and filesystem assertions and remove superseded helpers.

## Rollout Considerations

- This is an intentional breaking change to `okfkb install-skills`; document the
  new destination semantics and removal of `--force` in command help.
- Existing owned normal directories are updated automatically; unrelated skill
  directories remain untouched.
- No feature flag or data migration is required.

## Requirements Impact

No requirement traceability applicable to this change.
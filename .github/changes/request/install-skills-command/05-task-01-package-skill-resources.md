# Task 01: Package Complete Skill Resources

**Depends on**: None
**Estimated complexity**: Medium
**Type**: Feature
**Phase**: Phase 1 - Resource and Installer Foundation

## Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

- `AGENTS.md` - packaging architecture, project commands, and quality gate.
- `.github/guidelines/git-commit-message.guidelines.md` - every commit.
- `.github/guidelines/python-unittest.guidelines.md` - resource and wheel tests.
- `.github/guidelines/python-module-documentation.guidelines.md` - new package module documentation and typing.

## Objective

Make all seven canonical skill trees available as complete
`importlib.resources` content in installed wheels, with automated drift and
distribution checks.

## Files to Modify/Create

- `src/okf_schema/data/skills/__init__.py`
- `src/okf_schema/data/skills/okf-schema/`
- `src/okf_schema/data/skills/okfkb/`
- `src/okf_schema/data/skills/okfkb-distill/`
- `src/okf_schema/data/skills/okfkb-gardening/`
- `src/okf_schema/data/skills/okfkb-record-findings/`
- `src/okf_schema/data/skills/okfreq/`
- `src/okf_schema/data/skills/okfreq-gardening/`
- `pyproject.toml`
- `tests/test_skill_resources.py`

## Detailed Steps

1. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 01 --status in_progress --started-at now`.
2. Write failing function-based tests that recursively compare the seven
   canonical `skills/` trees with package resources, including nested references
   and assets.
3. Add a built-wheel assertion that opens the wheel archive and confirms every
   expected skill file is present under the installed package path.
4. Copy all seven canonical trees into the package resource namespace and adjust
   Hatch include configuration only as needed for wheel and sdist inclusion.
5. Run `uv run -- pytest tests/test_skill_resources.py` and fix failures.
6. Run `just preflight` and fix all issues until it completes successfully.
7. If requirement traceability becomes applicable, run
   `craftsman req update-coverage`; otherwise do not create requirement changes.
8. Run `craftsman agent update-task --prd /tmp/okf-schema-install-skills-command --id 01 --status coded_not_reviewed --completed-at now --coder-model "<model-name>" --summary "Packaged all canonical agent skill resources"`.
9. Commit using the discovered project convention, then let the Craftsman coder
   protocol apply centralized session and PRD trailers.

## Acceptance Criteria

- [ ] Package resources expose exactly the seven specified skill roots.
- [ ] Every nested canonical skill file, reference, and asset is represented in package resources.
- [ ] A built wheel contains the complete seven skill trees.
- [ ] Resource access and verification do not rely on repository-relative paths at runtime.
- [ ] Focused tests pass.
- [ ] Documentation is accurate for any maintained public package API introduced.
- [ ] `just preflight` passes after all coding is complete.

## Testing Strategy

Follow TDD and the red-green cycle on this task: write a failing test first,
confirm it fails, then implement minimal code to make it pass.

- **Test file**: `tests/test_skill_resources.py`
- **Test cases**: enumerate exactly seven resource roots; recursively compare
  canonical/package files and bytes; build a wheel and inspect all expected
  archive members; prove nested references/assets are retained.

## Notes

Treat repository-level `skills/` as the authoring source and package resources
as distribution copies. Keep parity checks deterministic and ignore no nested
content unless the specification explicitly excludes it.
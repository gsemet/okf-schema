# Maintain one coherent product across every delivery surface

Apply this guideline to every public behavior, CLI/API, configuration, schema,
validation rule, packaged resource, and workflow change in okf-schema, okfkb,
and okfreq. Bug fixes count as behavior changes.

## Responsibilities and canonical locations

| Surface | Audience and responsibility | Canonical location |
|---|---|---|
| Runtime | Executable behavior and public contracts, including versioned API docstrings and CLI help. | `src/okf_schema/` |
| Human documentation | Explain purpose, choices, prerequisites, runnable tasks, outputs, errors and limits. Tutorials teach; references specify. | `docs/source/`, with discovery in `README.md` |
| Agent skills | Supply operational knowledge without access to this tool's source checkout or documentation site. The installed CLI, the target project and bundled references are the available context. | `skills/<name>/SKILL.md` and its local resources |
| Generated project guidance | Give new projects correct defaults and maintenance rules. Existing projects retain their own policies; init must not overwrite them. | `src/okf_schema/data/` |
| Project requirements | State agreed observable behavior, preserve stakeholder intent, connect real implementation and tests, and exercise supported traceability features. | `requirements/config.yml`, `requirements/tiers/`, `requirements/guidelines/` |
| Concrete examples | Demonstrate realistic inputs, commands, outputs and failures with executable verification. Keep intentional bad data and lifecycle experiments disposable. | `examples/`, regenerated through `just refresh-all-examples` |
| Verification and packaging | Protect failure behavior, content preservation, installed-resource completeness, and example execution. | `tests/`, `pyproject.toml`, `justfile`, `.github/workflows/` |

## Required maintenance workflow

1. Identify the changed observable behavior and affected families. Read their
   local guidelines and existing requirement/scenario before editing.
2. Update implementation, CLI help/API docstrings and focused regression tests.
   Add source/test markers near actual evidence; high coverage percentages do
   not replace tests of malformed input, boundaries and non-mutation promises.
3. Review **every row above**. Update each affected surface in the same change.
   In the change summary, identify a surface as unaffected when that is the case
   and give a concrete reason. Never skip skills because documentation was updated.
4. Keep skill entrypoints concise and route to packaged references for command,
   configuration or recovery details. Relative links must resolve inside the
   installed skill; another family is an optional dependency unless explicitly
   shipped together. URLs may provide attribution, never essential instructions.
   Do not assume sibling installation paths or access to `src/` or `docs/`.
5. Human docs must tell a reader what to run, where outputs appear, what success
   and failure mean, and what the feature cannot conclude. Agent skills must
   additionally define ownership, decision criteria, repair and stopping rules.
   Keep command semantics consistent across both, without duplicating whole manuals.
6. Update an existing SwRS or create a bounded requirement through `okfreq new`
   when the contract changes. Preserve IDs, UUIDs, bodies and authored metadata;
   regenerate coverage instead of editing it. Follow the requirements guideline.
7. Record supported capabilities and evidence in
   `docs/source/explanation/project-feature-coverage.md`. Use applicable features
   in this repository's own requirements. For alternatives or destructive
   demonstrations (lifecycle transitions, exemptions, invalid data, alternate
   marker/coverage policies), use executable disposable examples. Never fabricate
   approvals, external tracker ownership, exemptions or coverage to fill a matrix.
8. Update example inputs or their generator, then regenerate outputs. Add new
   executable scenarios to the refresh target and tests so they cannot quietly
   drift. Explain intentional gaps rather than masking them with markers.
9. Run `just preflight` and review generated diffs. It may format files, update
   changelog and examples, and build reports/docs. Preserve legitimate generated
   changes, remove accidental artifacts, and report any check that could not run.

## Completion evidence

The final change summary or PR names the behavior, relevant requirements, human
entrypoints, packaged skill resources, example command, and validation results.
Distinguish defined marker linkage, actual test execution and stakeholder
approval. Do not claim complete traceability when any of these are missing.

## Use the guidance this project ships

For all requirement work, read
[`src/okf_schema/data/requirements/guidelines/requirements.guidelines.md`](../../src/okf_schema/data/requirements/guidelines/requirements.guidelines.md)
as the shared baseline, then
[`requirements/guidelines/requirements.guidelines.md`](../../requirements/guidelines/requirements.guidelines.md)
for this repository's paths, scopes and stricter checks. The local overlay may
specialize the baseline, not silently replace its navigation or logging duties.

When changing the baseline, review the local overlay, standalone skill guidance,
installed example guidance and tests in the same change. This repository must
exercise the installed workflow: `okfreq lint requirements` maintains generated
navigation at every tier/scope directory, while agents append meaningful entries
to `requirements/tiers/log.md`. `requirements/index.md` is an authored overview.
Use `lint --check` in CI to detect stale navigation without writes. Do not write
manual lists inside generated index markers or generate fictional log entries.

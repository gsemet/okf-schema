---
name: okfreq-gardening
description: 'Audit and improve an okfreq requirements bundle by finding missing traceability, stale requirements, broken hierarchy links, coverage gaps, and configuration drift while preserving authored content and generated-field ownership.'
metadata:
  keywords: [okfreq, requirements, traceability, gardening, audit, coverage, StRS, SwRS]
  url: https://github.com/gsemet/okf-schema
---

# okfreq gardening

This specialized workflow extends the foundational
[`okfreq` skill](../okfreq/SKILL.md). Read and apply that skill first so the
requirements goal, StRS-to-SwRS model, project-guideline precedence, and
traceability semantics remain in force throughout gardening.

Perform an explicit, evidence-based maintenance pass over an `okfreq` bundle.
The primary users are coding agents working on brownfield projects where source
code, tests, and requirements have drifted apart. The workflow discovers gaps,
proposes safe changes, and validates the result. It does not silently invent
requirements, evidence, IDs, UUIDs, lifecycle transitions, or coverage.

Invoke this skill only when the user asks to audit, garden, refresh, reconcile,
or maintain an `okfreq` requirements base. Do not run it proactively during an
unrelated implementation task.

## Non-negotiable boundaries

- Resolve the bundle root before anything else: it is the directory that owns
   `config.yml`. Prefer a top-level `requirements/`; otherwise resolve the agent
   configuration directory, using `.agents/` when it exists and `.github/` only
   as a fallback. Never prefer `.github/` over an existing `.agents/` directory,
   and do not create both locations for the same configuration.
- Treat the bundle as split. The bundle root owns `config.yml`, `guidelines/`,
   and generated reports; `<bundle>/tiers/` owns `_schema/`, `index.md`,
   `log.md`, and the level folders. Read `config.yml` and every file in
   `<bundle>/tiers/_schema/` before editing anything.
- Preserve requirement IDs, UUIDs, authored frontmatter, unknown properties,
  YAML comments, and Markdown bodies.
- Never hand-edit `derived_by`, `implemented_in_files`, `tested_in_files`, indexes,
  or reports. Use explicit `okfreq` commands for generated data.
- Never claim implementation or test coverage without source evidence and
  markers. Markers are links, not proof that tests pass.
- Never change lifecycle or approval state as an incidental edit.
- Never renumber existing IDs. New IDs must be collision-safe and stable.
- Imported requirements remain read-only by default; change them only through an
  explicit migration or import operation.
- Preserve unrelated user work and inspect the worktree before writing.

## Phase 1 — Discover project rules and scope

1. Resolve the bundle root. Prefer an explicit path; otherwise look for
   `requirements/`, then `<agent-config>/requirements/`, where `<agent-config>`
   is `.agents/` when it exists and `.github/` otherwise. Confirm the choice by
   the presence of `config.yml`. Stop if no unique bundle exists.
2. Read the nearest `AGENTS.md`, the bundle's own
   `guidelines/requirements.guidelines.md`, any other applicable guidelines,
   `config.yml`, and every schema in `tiers/_schema/`. If the bundle guideline
   is absent, use the `okfreq` skill's bundled reference guideline as the
   fallback; a project-local guideline always takes precedence.
3. Confirm the bundle resolves as expected before auditing content. Run
   `okfreq validate <bundle> --prose`; a traceback or a missing-schema error means the
   layout and the tool disagree, and that drift is the first finding to fix.
3. Read the project task runner and CI configuration to identify validation and
   test commands. Do not assume a universal runner.
4. Record configured levels, parent relationships, ID policy, lifecycle values,
   marker keywords, generated-field ownership, and scope mappings.
5. Inspect `git status` so pre-existing changes are not attributed to gardening.

## Phase 2 — Establish a read-only baseline

Run the project-prescribed validation and test checks before changing files.
Then inspect requirements frontmatter before bodies and inventory:

- every requirement by ID, UUID, level, scope, origin, and lifecycle;
- authored `derives_from` and `depends_on` relationships;
- generated `derived_by`, implementation, and test fields;
- verification methods and criteria;
- unknown producer metadata and preservation-sensitive comments;
- source and test files covered by each configured scope.

Use the following commands as appropriate:

```console
okfreq status .
okfreq validate . --prose
okfreq lint . --prose
okfreq index .
okfreq graph . --json
okfreq trace . --json
```

Keep schema errors, graph errors, marker errors, missing IDs, lifecycle counts,
and scan warnings as separate findings.

## Phase 3 — Repair structural and graph issues

1. Identify malformed frontmatter, missing required fields, invalid UUIDs, invalid
   levels, invalid lifecycle values, and unknown hierarchy targets.
2. Detect orphaned upper-level requirements and requirements whose parent level
   violates the configured hierarchy.
3. Use `okfreq graph` to inspect reverse derivation. Rebuild generated
   `derived_by` only through `okfreq update-coverage` after previewing it.
4. Never repair an uncertain relationship by guessing. Report it as an open
   discrepancy and ask for a decision.
5. Preserve all authored and unknown metadata while making approved repairs.

## Phase 4 — Audit source and test traceability

Run `okfreq trace . --json` and classify results:

- `implemented` — source files containing implementation markers;
- `tested` — test files containing test markers;
- `missing_ids` — markers that reference no known requirement;
- `duplicates` — the same ID marked twice inside one file; markers for one ID in
  several distinct files are legitimate multi-file coverage, not a duplicate;
- `non_leaf` — markers on an upper-level requirement, normally a warning;
- `warnings` — missing or otherwise incomplete scan locations.

For each requirement, determine whether it has credible implementation and test
links. Distinguish these cases:

1. **Existing behavior, missing marker:** propose adding the correct marker near
   the relevant function, class, module, or test.
2. **New behavior with no requirement:** propose a new configured-level
   requirement through `okfreq new`, link it with `derives_from`, and do not
   repurpose an existing ID.
3. **Requirement with no matching behavior:** report `req_not_in_code`; do not
   delete or silently deprecate it.
4. **Behavior delivered by shipped non-code content:** when a requirement is
   satisfied by packaged prompt, skill, or data files, add that location to the
   relevant scope in `config.yml` and place the marker in the file itself, using
   a comment form the format allows. Do not attribute it to unrelated code.
5. **Infrastructure or generated code:** record an explicit exemption rationale
   instead of forcing a misleading marker.

Ask for confirmation before modifying source, tests, authored requirement
content, or scope mappings. Add markers in comments appropriate for the language
and keep them close to the behavior they identify.

### Tier-specific authoring contract

When an approved gap requires `okfreq new`, preserve the distinct generated
formats instead of applying one generic requirement template:

- **StRS — stakeholder intent:** provide one stakeholder-observable `SHALL`
  statement as `--description` and the stakeholder's underlying outcome as
  `--user-need`. Complete `EARS Expression`, `Normative behavior`, `User Need`,
  and `Rationale and constraints`. Do not add SwRS scenarios, verification
  notes, implementation markers, or test markers to an StRS.
- **SwRS — software behavior:** provide one observable, bounded `SHALL`
  response as `--description` and at least one valid StRS parent with
  `--derives-from`. Complete nominal and boundary/failure GIVEN-WHEN-THEN
  scenarios plus objective verification notes. Do not add a `User Need` or
  stakeholder-constraints section to an SwRS.

Treat every angle-bracket item emitted by the scaffold as an explicit authoring
gap. Replace it with evidence-based content or leave it visible and report the
requirement as incomplete; never delete a placeholder merely to silence prose
validation. Use the generated frontmatter as-is: `user_need` belongs to StRS,
while annotation exemption intent belongs to SwRS.

## Phase 5 — Update generated coverage safely

After markers are reviewed, preview generated updates:

```console
okfreq update-coverage . --check
okfreq update-coverage . --diff
okfreq update-coverage .
```

The command may update only fields owned by `okfreq`: reverse derivation and
coverage fields. Verify that bodies, comments, quotes, IDs, UUIDs, unknown
properties, authored derivations, dependencies, and verification criteria are
unchanged. If a generated update would overwrite external ownership, stop and
report the conflict.

## Phase 6 — Lifecycle and verification audit

Treat `draft`, `proposed`, `approved`, `deprecated`, and `superseded` as distinct.
An approved requirement needs configured verification information and successful
structural validation; a marker alone is insufficient. Lifecycle changes are
explicit and confirmed:

```console
okfreq archive REQUIREMENT-ID --yes
okfreq supersede OLD-ID REPLACEMENT-ID --yes
```

Archive never deletes. Supersession requires a real replacement target. Do not
mutate lifecycle state merely because prose, coverage, or indexes changed.

## Phase 7 — Reports and final validation

Generate separate metrics rather than a composite score:

Write generated reports to the project's `dist/` directory, never into the
requirements bundle or `tiers/`:

```console
okfreq generate-report <bundle> --output <project>/dist/requirements-report.json
okfreq generate-report <bundle> --output <project>/dist/requirements-report.md --format markdown
```

Report at least:

- schema and structural health;
- hierarchy and graph errors;
- implementation marker coverage;
- test marker coverage;
- missing, duplicate, and non-leaf references;
- lifecycle counts;
- unresolved discrepancies and exemptions.

Run the project-prescribed preflight after all approved changes. At minimum,
run `okfreq validate --prose`, `okfreq lint --prose`, and the normal project
tests. Prose findings remain advisory, but unresolved scaffold placeholders must
be reported as authoring gaps.

## Final report

Return a concise summary containing:

1. baseline errors and warnings;
2. requirements inspected and discrepancies by category;
3. markers added or proposed in source and tests;
4. generated fields updated and preview commands used;
5. lifecycle changes explicitly confirmed;
6. files changed and files intentionally preserved;
7. validation and test commands with results; and
8. unresolved questions requiring human decisions.

Do not claim that traceability is complete when evidence is missing or tests did
not run successfully.

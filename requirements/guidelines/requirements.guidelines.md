# Requirements guidelines

This file specializes the [shipped baseline](../../src/okf_schema/data/requirements/guidelines/requirements.guidelines.md)
for this repository. Read and follow that baseline first: it is the same guidance
installed into other projects. The rules below supply our paths, scopes and checks.

## Before editing

- Resolve the requirements bundle as `requirements/` in this repository, with its
  documents under `requirements/tiers/`.
- Read `requirements/config.yml` and every schema under
  `requirements/tiers/_schema/` before changing requirement documents.
- Use the configured scopes: `core`, `okfkb`, and `okfreq`.
- Preserve requirement IDs, UUIDs, authored fields, unknown metadata, comments,
  and Markdown bodies.

## While editing

- Use the frontmatter `title` verbatim as the first Markdown heading (`## Title`).
  Keep the heading synchronized when renaming a requirement; EARS describes
  the statement format, not the document title.

- Store stakeholder requirements under `requirements/tiers/strs/<scope>/` and
  software requirements under `requirements/tiers/swrs/<scope>/`.
- Use the filename and ID convention already established by the bundle, such as
  `SwRS-OKFSCHEMA-OKFREQ-002.md`.
- Author parent relationships with `derives_from`; do not hand-edit generated
  `derived_by`, `implemented_in_files`, or `tested_in_files` fields.
- For leaf software requirements, add `@implements_req <ID>` markers close to
  the implementation and `@tests_req <ID>` markers close to corresponding
  tests. Do not use source markers on stakeholder or other non-leaf levels. The project
  uses `linked-swrs-and-validation-test`: add a direct StRS marker only to a real
  stakeholder validation test.
- Keep core `okf-schema`, knowledge-base `okfkb`, and requirements `okfreq`
  concerns in their configured scopes rather than combining unrelated claims.

## Tier-specific authoring formats

- For an StRS, pass a stakeholder-observable `SHALL` statement as
  `--description` and the underlying outcome as `--user-need`. Complete the
  generated normative behavior, user need, and rationale/constraints sections.
  Do not add SwRS scenarios or verification notes.
- For an SwRS, pass one observable, bounded `SHALL` response as `--description`
  and at least one valid StRS ID with `--derives-from`. Complete both generated
  GIVEN-WHEN-THEN scenarios and the objective verification notes. Do not add an
  StRS user-need or stakeholder-constraints section.
- Replace every angle-bracket placeholder before review. A remaining placeholder
  is an explicit gap, not content to delete or silently reinterpret.

## After editing

Run the following from the repository root:

```console
okfreq update-coverage requirements
okfreq validate requirements --prose --check-links --project-root .
okfreq lint requirements --prose --check-links --project-root .
okfreq trace requirements --json
```

Then run the complete project quality gate:

```console
just preflight
```

Do not claim complete traceability when a non-exempt leaf requirement lacks
source or test markers, when markers reference unknown IDs, or when
validation/tests fail.

## Exercise the project contract

- Keep the three supported generated fields enabled and refresh them through
  `okfreq update-coverage`; `--check` must fail when they are stale.
- Keep the strict StRS coverage mode and direct validation-test evidence current.
- Maintain authored `documentation_files`, `agent_skill_files`, `example_files`,
  dependencies and verification criteria as actual existing project evidence.
- Review `docs/source/explanation/project-feature-coverage.md` for feature usage.
  Use the disposable showcase for conflicting policies, external demo metadata,
  lifecycle operations and exemptions rather than inventing live project states.
- Follow the registered product maintenance guideline for every behavior change.

## Navigation and history in this repository

- Preserve the authored overview at `requirements/index.md`.
- Run `okfreq lint requirements` to regenerate marked navigation blocks in
  `requirements/tiers/index.md`, tier folders and all scope folders, including
  `requirements/tiers/swrs/okfreq/index.md`.
- Append substantive requirement changes, affected IDs/links, rationale and
  verification results to `requirements/tiers/log.md`. Preserve earlier entries.
- CI runs `okfreq lint requirements --check --check-links --project-root .`;
  do not hand-maintain generated lists or treat the log as generated content.

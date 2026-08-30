# Requirements guidelines

These guidelines govern the `okfreq` requirements layer in this repository.

## Before editing

- Resolve the requirements bundle as `requirements/` in this repository, with its
  documents under `requirements/tiers/`.
- Read `requirements/config.yml` and every schema under
  `requirements/tiers/_schema/` before changing requirement documents.
- Use the configured scopes: `core`, `okfkb`, and `okfreq`.
- Preserve requirement IDs, UUIDs, authored fields, unknown metadata, comments,
  and Markdown bodies.

## While editing

- Store stakeholder requirements under `requirements/tiers/strs/<scope>/` and
  software requirements under `requirements/tiers/swrs/<scope>/`.
- Use the filename and ID convention already established by the bundle, such as
  `SwRS-OKFSCHEMA-OKFREQ-002.md`.
- Author parent relationships with `derives_from`; do not hand-edit generated
  `derived_by`, `implemented_in_files`, or `tested_in_files` fields.
- For leaf software requirements, add `@implements_req <ID>` markers close to
  the implementation and `@tests_req <ID>` markers close to corresponding
  tests. Do not use source/test markers on stakeholder or other non-leaf levels.
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
okfreq validate requirements --prose
okfreq lint requirements --prose
okfreq trace requirements --json
```

Then run the complete project quality gate:

```console
just preflight
```

Do not claim complete traceability when a non-exempt leaf requirement lacks
source or test markers, when markers reference unknown IDs, or when
validation/tests fail.

---
name: okfreq-requirements
description: 'Safe, non-destructive guidance for agents maintaining okfreq requirement bundles.'
---

# okfreq requirements

<!-- @implements_req SwRS-OKFSCHEMA-OKFREQ-002 -->

## Bundle layout

The bundle root owns `config.yml`, this `guidelines/` folder, and generated
reports. `tiers/` owns `_schema/`, `index.md`, `log.md`, and the configured level
folders such as `strs/` and `swrs/`. Requirement documents live only under
`tiers/`.

## Before editing

- Read the bundle's `config.yml` and every schema under `tiers/_schema/`.
- Use `okfreq` for creation, validation, indexing, traceability, and lifecycle changes.
- Read `okfreq --help` for the authoritative command options.

## While editing

- Create requirements with `okfreq new` so IDs, UUIDs, and folders follow the configuration.
- Preserve comments, Markdown body text, unknown frontmatter, IDs, and UUIDs.
- Do not hand-edit `derived_by`, coverage fields, indexes, or reports.
- Never renumber existing IDs or UUIDs, and never claim coverage without markers or evidence.
- Put implementation and test markers only on leaf software requirements, not
  on stakeholder or other non-leaf levels.
- Do not change lifecycle or approval state as an incidental edit.

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

- Run `okfreq validate --prose` and `okfreq lint --prose` so unfinished
  scaffold placeholders remain visible as advisory findings.
- Preview generated updates with the command's `--check` or `--diff` options before applying them.
- Write generated reports to the bundle root, never into `tiers/`.
- Treat `draft`, `proposed`, and `approved` as distinct lifecycle states.
- Run the project's own test suite; a marker is a link, not proof that a test passes.

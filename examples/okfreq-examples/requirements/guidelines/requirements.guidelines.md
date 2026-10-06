---
name: okfreq-requirements
description: 'Safe, non-destructive guidance for agents maintaining okfreq requirement bundles.'
---

# okfreq requirements

<!-- @implements_req SwRS-OKFSCHEMA-OKFREQ-002 -->

## Bundle layout

The bundle root owns `config.yml`, this `guidelines/` folder and an optional
human-authored `index.md` overview. `tiers/` owns `_schema/`, `index.md`,
`log.md` and the configured level folders, such as `strs/` and `swrs/`.
Requirement documents live only under `tiers/`.

## Before editing

- Read the bundle's `config.yml` and every schema under `tiers/_schema/`.
- Use `okfreq` for creation, validation, indexing, traceability, and lifecycle changes.
- Read `okfreq --help` for the authoritative command options.
- When backfilling an existing feature, inspect agreed documentation, source and
  tests first. Propose intended behavior with evidence and open questions;
  do not assume every implemented detail is a desired requirement.

## While editing

- Use the frontmatter `title` verbatim as the first Markdown heading (`## Title`).
  Keep the heading synchronized when renaming a requirement; EARS describes
  the statement format, not the document title.

- Store stakeholder requirements under `tiers/strs/<scope>/` and software
  requirements under `tiers/swrs/<scope>/`.
- Use the filename and ID convention established by the bundle.
- Author parent relationships with `derives_from`; never hand-edit generated
  `derived_by`, `implemented_in_files`, or `tested_in_files` fields.
- For leaf software requirements, add `@implements_req <ID>` markers near the
  implementation and `@tests_req <ID>` markers near corresponding tests. Do not
  use source markers on stakeholder or other non-leaf levels. A real direct
  stakeholder validation test may carry an StRS test marker when the configured
  coverage mode requires it.

## Generated navigation metadata

`okfreq init` adds `x-okf-link` annotations to the generated schemas. They
declare requirement filename-stem links and project-relative source/test links,
including advisory `id_marker`, marker prefixes, tooltip/preview field hints,
and source/test line-number hints. These annotations guide editors and other
consumers; they do not execute tests or prove coverage. Existing schemas are
preserved and are not migrated by `okfreq init`.

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

- Run `okfreq validate --prose`, then `okfreq lint --prose` so unfinished
  scaffold placeholders remain visible as advisory findings.
- Preview generated updates with the command's `--check` or `--diff` options
  before applying them.
- Write generated reports to explicit project `dist/` paths with
  `--output-json` and `--output-summary-md`, never into `tiers/`.
- Missing or malformed requirement frontmatter and missing IDs fail explicitly;
  repair the document instead of dropping it from the reported inventory.
- Treat `draft`, `proposed`, and `approved` as distinct lifecycle states.
- Run the project's own test suite; a marker is a link, not proof that a test passes.

## Navigation and change history

- Run `okfreq lint <bundle>` after adding, moving, removing or changing a
  requirement. It generates `tiers/index.md`, configured tier indexes and
  indexes in every directory containing requirements or their descendants,
  including scope folders such as `tiers/swrs/core/index.md`.
- Only content between `<!-- okfreq:index:start -->` and
  `<!-- okfreq:index:end -->` is generated. Do not hand-edit that block.
  Frontmatter, introductions and authored text outside it are preserved.
  The optional `<bundle>/index.md` overview is authored and is not generated.
- Preview with `okfreq lint <bundle> --diff`; use `--check` for read-only CI
  verification. Check mode fails when navigation is absent or stale. Structural
  validation must pass before lint writes any indexes.
- Agents append a dated entry to `<bundle>/tiers/log.md` after substantive
  requirement changes: record affected IDs or relative links, what changed,
  why it changed, decisions or open questions and actual verification results.
  Put newest dates first and append to an existing date section when appropriate.
- The canonical filename is `log.md`, not `logs.md`. It is authored history:
  lint must never regenerate or overwrite it. Do not add a history entry solely
  because identical generated artifacts were refreshed, or invent approvals or
  test results. Preserve previous entries.

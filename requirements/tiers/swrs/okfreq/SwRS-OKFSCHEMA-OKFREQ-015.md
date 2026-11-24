---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-015
uuid: 17cbd1c6-f25f-4f38-be89-fe4304a05a28
title: Measure StRS acceptance paths with declared scenarios
description: 'When a bundle uses strs_test_coverage_mode linked-swrs-and-acceptance-paths,
  okfreq SHALL count each StRS main path and each SwRS transition declared in scenarios:
  as tested or accepted only through test markers that name it with a #S<n> fragment,
  report the paths and transitions in coverage, and report the markers and requirements
  that break this rule.'
project: okf-schema
scope: okfreq
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests of okfreq in each coverage mode
  and the live requirements bundle, which uses the acceptance mode with no
  finding.
documentation_files:
- docs/source/explanation/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-frontmatter.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
- skills/okfreq-setup/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
scenarios:
- id: S1
  title: Activate the mode and keep the old modes
- id: S2
  title: Declare scenarios in the frontmatter
- id: S3
  title: Read three marker kinds and the scenario fragment
- id: S4
  title: Apply one fragment rule to every test marker
- id: S5
  title: Refuse an acceptance marker on a software requirement
- id: S6
  title: Count paths, transitions and generated evidence
- id: S7
  title: Warn about a stakeholder requirement without paths or acceptance test
- id: S8
  title: Add scenarios to an approved requirement
- id: S9
  title: Report paths and transitions
- id: S10
  title: Pre-fill scenarios in new requirements
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq.py
default_owner_email: gaetan@xeberon.net
---

## Measure StRS acceptance paths with declared scenarios

### Normative behavior

When a bundle uses strs_test_coverage_mode linked-swrs-and-acceptance-paths, okfreq SHALL count each StRS main path and each SwRS transition declared in scenarios: as tested or accepted only through test markers that name it with a #S<n> fragment, report the paths and transitions in coverage, and report the markers and requirements that break this rule.

### Scenario: Activate the mode and keep the old modes

- GIVEN a bundle whose `config.yml` sets `strs_test_coverage_mode` to `linked-swrs`,
  `linked-swrs-and-validation-test` or `linked-swrs-and-acceptance-paths`
- WHEN `okfreq` loads, validates, traces, updates coverage or reports
- THEN the new mode is accepted and an unsupported mode is refused naming the three modes; in
  the old modes `scenarios:` and `@accepts_req` count toward nothing, and only the every-mode
  changes appear (report `format_version` 2, the trace `accepted` count, the `@accepts_req`
  retirement guard, the scaffold declarations and the removal of
  `tested_in_files`/`accepted_in_files` from a StRS)

### Scenario: Declare scenarios in the frontmatter

- GIVEN a StRS or a SwRS whose frontmatter lists `scenarios:` entries `{id: S<n>, title}`
- WHEN the bundle is validated or its coverage is regenerated
- THEN the base schema refuses a malformed entry in every mode, the acceptance mode also refuses
  duplicate ids, and `update-coverage` keeps the authored list unchanged

### Scenario: Read three marker kinds and the scenario fragment

- GIVEN `@implements_req`, `@tests_req` and `@accepts_req` markers (or their configured
  keywords) whose identifier may be followed by `#S<n>`
- WHEN the markers are scanned
- THEN test markers are read only in `test_dirs`, the fragment is `#S` and digits glued to the
  ID, any other suffix leaves the marker fragmentless, the scan lists `accepted` and
  `scenario_markers` with their line, an older `config.yml` gets the default `accepts` keyword,
  and two kinds sharing one keyword are refused

### Scenario: Apply one fragment rule to every test marker

- GIVEN the acceptance mode and a test marker on a StRS or a SwRS
- WHEN the bundle is validated
- THEN a marker on a requirement that declares `scenarios:` counts only with a declared `#S<n>`,
  a fragmentless marker on a requirement that declares none counts for the whole requirement,
  every other combination is an error naming the file, line, configured keyword and declared
  ids, and markers on project-added tiers keep their earlier handling

### Scenario: Refuse an acceptance marker on a software requirement

- GIVEN the acceptance mode and an `@accepts_req` marker naming a SwRS, or a SwRS schema that
  does not refuse `accepted_in_files`
- WHEN the bundle is validated
- THEN the marker is reported with the description of the SwRS schema, or the schema is reported
  once with the declaration to add, and validation fails

### Scenario: Count paths, transitions and generated evidence

- GIVEN the acceptance mode and counting `@tests_req` and `@accepts_req` markers
- WHEN coverage is computed and `update-coverage` runs
- THEN a StRS is tested when every declared path has a `@tests_req`, accepted when every
  declared path has an `@accepts_req`, covered when its linked SwRS are covered and it is
  accepted; a SwRS is covered when every declared transition has a test; and
  `tested_in_files`/`accepted_in_files` list only the files of counting markers when listed in
  `generated_fields`

### Scenario: Warn about a stakeholder requirement without paths or acceptance test

- GIVEN the acceptance mode and a live StRS without `scenarios:` or without a counting
  `@accepts_req`
- WHEN `okfreq validate` or `okfreq lint` runs
- THEN `W003` quotes the main-path and scenario headings with the `scenarios:` block to paste,
  `W004` asks for an acceptance test, neither changes the exit status, and a deprecated or
  superseded StRS gets neither

### Scenario: Add scenarios to an approved requirement

- GIVEN an approved StRS with `approved_by` and `approved_at`
- WHEN only `scenarios:` is added to its frontmatter
- THEN the requirement still validates with its approval record unchanged

### Scenario: Report paths and transitions

- GIVEN the acceptance mode
- WHEN the JSON or Markdown report is generated
- THEN each StRS reports `paths`, `tested`, `accepted`, `tests` and `acceptance_tests`, each
  SwRS that declares transitions reports `transitions`, the aggregate reports `paths`, only
  counting markers feed `marker_coverage`, the Markdown shows the path and transition columns,
  and every report validates against `report_schema()` with `format_version` 2

### Scenario: Pre-fill scenarios in new requirements

- GIVEN the acceptance mode
- WHEN `okfreq new strs` or `okfreq new swrs` writes a requirement
- THEN its `scenarios:` list matches the placeholder headings of the body it writes, a StRS body
  gains a `### Main paths` section, and in the old modes the output is unchanged

### Verification notes

- Method: unit and CLI tests of `okfreq` in each coverage mode, and the live bundle of this
  repository, which uses the acceptance mode.
- Criteria: each scenario has a test marked with its fragment; `okfreq validate requirements`
  reports no error, no `W003` and no `W004`.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

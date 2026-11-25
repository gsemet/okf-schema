---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-015
uuid: b5ca6f03-9c71-49d6-a114-c25e07fe3d82
title: Measure StRS acceptance paths with declared scenarios
description: 'When linked-swrs-and-acceptance-paths mode is enabled, okfreq SHALL
  track declared scenarios and #S<n> marker fragments, separate @tests_req and @accepts_req
  evidence, enforce whole-StRS acceptance waivers, and emit format_version 2 reports.'
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
scenarios:
- id: S1
  title: 'Track declared scenarios and #S<n> marker fragments'
- id: S2
  title: Separate @tests_req and @accepts_req evidence and enforce tier rules
- id: S3
  title: Apply whole-StRS acceptance waivers and preserve legacy modes
- id: S4
  title: Emit format_version 2 reports, W003/W004 warnings, and mode-aware
    templates
documentation_files:
- docs/source/explanation/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-frontmatter.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-cli.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
- skills/okfreq-setup/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/tests/test_acceptance_export.py
verification_method: test
verification_criteria: >-
  Unit, CLI, documentation, example, and installed-wheel acceptance tests verify
  Rules 1 to 9 across all three coverage modes, fragment validation, whole-StRS
  waivers, W003/W004 diagnostics, and format_version 2 JSON/Markdown reports.
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_examples.py
- tests/test_okfreq.py
default_owner_email: gaetan@xeberon.net
---

## Measure StRS acceptance paths with declared scenarios

### Normative behavior

When `strs_test_coverage_mode: linked-swrs-and-acceptance-paths` is configured,
`okfreq` SHALL:

1. Preserve legacy behavior unchanged under `linked-swrs` and
   `linked-swrs-and-validation-test` (Rule 1).
2. Validate authored `scenarios:` lists (`id` matching `^S[1-9][0-9]*$`, unique,
   non-blank `title`), whole-StRS `acceptance_exemption` /
   `acceptance_exemption_reason` waivers, and reject duplicate marker keywords
   (Rules 2, 3).
3. Scan `markers.accepts` (default `@accepts_req`) in `test_dirs`, capture
   optional `#S<n>` fragments (`S[0-9]+` at a non-identifier boundary), and
   record `accepted` and `scenario_markers` in `marker_scan` (Rule 3).
4. Reject `@accepts_req` on SwRS via schema validation, reject missing or
   unknown `#S<n>` fragments on requirements that declare `scenarios:`, and
   reject `#S<n>` fragments on requirements that declare no `scenarios:` (Rule 4).
5. Compute independent `tested` and `accepted` counters per StRS and per-transition
   coverage per SwRS, count individually exempted linked SwRS as `exempt`,
   generate `tested_in_files` and `accepted_in_files` on StRS only in the new
   mode, and preserve authored waivers during `update-coverage` (Rules 5, 7).
6. Emit `W003` (missing `scenarios:` with pasteable block) and `W004` (missing
   acceptance test unless waived) warnings, refuse draft retirement when
   `@accepts_req` references the draft, emit `format_version: 2` JSON and
   Markdown reports, and pre-fill `scenarios:` and `### Main paths` in
   `okfreq new` templates (Rules 6, 8, 9).

### Scenario S1: Track declared scenarios and #S<n> marker fragments

- GIVEN a bundle in `linked-swrs-and-acceptance-paths` mode with requirements declaring `scenarios:` and test files carrying `#S<n>` fragments
- WHEN `okfreq trace`, `okfreq validate`, and `okfreq update-coverage` run
- THEN valid fragments count toward their declared scenarios, missing or unknown fragments fail validation and do not count, and fragments on requirements without `scenarios:` fail validation.

### Scenario S2: Separate @tests_req and @accepts_req evidence and enforce tier rules

- GIVEN a StRS with declared main paths and linked SwRS in `linked-swrs-and-acceptance-paths` mode
- WHEN tests carry `@tests_req` and `@accepts_req` markers
- THEN `tested` and `accepted` counters are computed independently, StRS `tested_in_files` and `accepted_in_files` record only counting markers, and `@accepts_req` on a SwRS fails validation through the SwRS schema.

### Scenario S3: Apply whole-StRS acceptance waivers and preserve legacy modes

- GIVEN a StRS carrying `acceptance_exemption: true` and a non-blank `acceptance_exemption_reason`, and another bundle using `linked-swrs` or `linked-swrs-and-validation-test`
- WHEN `okfreq validate` and `okfreq generate-report` run on each bundle
- THEN the waived StRS suppresses `W004` and counts as covered once its linked SwRS are covered or exempted without fabricating `accepted` counts, while legacy modes ignore `@accepts_req` and `#S<n>` fragments.

### Scenario S4: Emit format_version 2 reports, W003/W004 warnings, and mode-aware templates

- GIVEN a bundle in `linked-swrs-and-acceptance-paths` mode with undeclared paths, missing acceptance tests, or newly scaffolded requirements
- WHEN `okfreq validate`, `okfreq generate-report`, `okfreq retire`, and `okfreq new` run
- THEN `W003` and `W004` report actionable guidance, `retire` refuses drafts referenced by `@accepts_req`, `generate-report` emits schema-valid `format_version: 2` JSON and Markdown reports, and `okfreq new` pre-fills `scenarios:` and `### Main paths` in the new mode.

### Verification notes

- Method: test
- Criteria: Unit, CLI, documentation, example, and installed-wheel acceptance tests verify Rules 1 to 9 across all three coverage modes, fragment validation, whole-StRS waivers, W003/W004 diagnostics, and format_version 2 JSON/Markdown reports.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

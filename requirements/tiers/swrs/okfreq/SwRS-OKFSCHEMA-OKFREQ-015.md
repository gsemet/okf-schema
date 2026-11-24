---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-015
uuid: fbb47c9a-8e25-4801-80f4-06c545138f16
title: Measure StRS acceptance paths
description: When strict stakeholder coverage runs in mode
  linked-swrs-and-acceptance-paths, okfreq SHALL read the main paths of each
  StRS and the scenarios of each requirement, count the markers that carry a
  scenario fragment into two independent tested and accepted counters, and
  report them without changing the coverage of any other mode.
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
verification_criteria: Focused regression tests and the complete project
  preflight pass.
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
scenarios:
- id: S1
  title: Count tested and accepted paths independently
- id: S2
  title: Refuse a marker that cannot count
- id: S3
  title: Warn when acceptance cannot be reached
- id: S4
  title: Report the paths and transitions
- id: S5
  title: Leave the other modes unchanged
- id: S6
  title: Keep the approval when only scenarios are declared
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq_acceptance_paths.py
- tests/test_okfreq_acceptance_paths_cli.py
- tests/test_okfreq_docs.py
default_owner_email: gaetan@xeberon.net
---

## Measure StRS acceptance paths

### Normative behavior

When strict stakeholder coverage runs in mode linked-swrs-and-acceptance-paths, okfreq SHALL read the main paths of each StRS and the scenarios of each requirement, count the markers that carry a scenario fragment into two independent tested and accepted counters, and report them without changing the coverage of any other mode.

### Scenario S1: Count tested and accepted paths independently

- GIVEN a bundle in mode `linked-swrs-and-acceptance-paths`, a StRS declaring
  scenarios S1 and S2 as main paths, and markers `@tests_req StRS-X#S1` and
  `@accepts_req StRS-X#S2`
- WHEN `okfreq trace`, `okfreq update-coverage` or `okfreq generate-report` runs
- THEN the StRS reports one of two paths tested and one of two accepted, its
  `tested` and `accepted` booleans stay false, its `tested_in_files` and
  `accepted_in_files` list only the files whose markers count, and it is covered
  only when every linked SwRS is covered or exempt and every path is accepted or
  the whole StRS carries a justified `acceptance_exemption`

### Scenario S2: Refuse a marker that cannot count

- GIVEN a requirement that declares `scenarios:` and a `@tests_req` or
  `@accepts_req` marker without a `#S<n>` fragment, with an unknown fragment, or
  an `@accepts_req` marker naming a SwRS
- WHEN `okfreq validate` or `okfreq lint` runs
- THEN the command reports an error that names the marker, its file and line and
  the declared scenarios, exits non-zero, and does not count the marker

### Scenario S3: Warn when acceptance cannot be reached

- GIVEN a live StRS without `scenarios:`, a live StRS without a counting
  `@accepts_req` marker, or a StRS with `acceptance_exemption: true` and a blank
  `acceptance_exemption_reason`
- WHEN `okfreq validate` runs
- THEN it prints `W003` quoting the headings found under `### Main paths` and the
  `scenarios:` block to paste, and `W004` naming the missing acceptance test,
  both without changing the exit status; a justified waiver suppresses `W004`,
  and a blank reason is an error

### Scenario S4: Report the paths and transitions

- GIVEN a bundle in mode `linked-swrs-and-acceptance-paths` with markers
- WHEN `okfreq generate-report` runs
- THEN the JSON report validates against `report_schema`, each StRS carries
  `paths: {total, tested, accepted}` and `acceptance_tests`, each SwRS lists its
  tested and missing transitions, and the Markdown report adds the path columns
  and the missing-transitions column

### Scenario S5: Leave the other modes unchanged

- GIVEN a bundle in mode `linked-swrs` or `linked-swrs-and-validation-test`,
  with `scenarios:`, fragments or `@accepts_req` markers present
- WHEN `okfreq validate`, `okfreq update-coverage`, `okfreq new` or
  `okfreq generate-report` runs
- THEN no fragment error, `W003` or `W004` is raised, no marker is required or
  counted for scenarios, and the output of `okfreq new` stays unchanged

### Scenario S6: Keep the approval when only scenarios are declared

- GIVEN an approved StRS whose frontmatter only gains `scenarios:`
- WHEN `okfreq validate` runs
- THEN it reports no error and the `approved_by` and `approved_at` fields stay
  valid, so the edit needs no new approval and only the project log names the
  owner's agreement

### Verification notes

- Method: test
- Criteria: `tests/test_okfreq_acceptance_paths.py`,
  `tests/test_okfreq_acceptance_paths_cli.py` and `tests/test_okfreq_docs.py`
  cover every scenario against the library and the commands, and the showcase
  walks the mode in a disposable project.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

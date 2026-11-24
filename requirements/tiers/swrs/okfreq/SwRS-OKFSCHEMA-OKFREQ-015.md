---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-015
uuid: 91fb4b82-321f-427d-8bcb-71b70297b878
title: Measure stakeholder acceptance through declared main paths
description: When a project selects mode linked-swrs-and-acceptance-paths,
  okfreq SHALL derive stakeholder acceptance from @accepts_req markers naming
  declared main paths, and SHALL report per-path coverage, findings and report
  format 2 that the mode defines.
project: okf-schema
scope: okfreq
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
scenarios:
- id: S1
  title: Select the acceptance-paths mode
- id: S2
  title: Declare scenarios and waive acceptance
- id: S3
  title: Read two test verbs and their scenario fragments
- id: S4
  title: Decide what each marker counts
- id: S5
  title: Compute paths, transitions and coverage
- id: S6
  title: Guide the author with W003 and W004
- id: S7
  title: Report paths and pre-fill scenarios
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
depends_on:
- SwRS-OKFSCHEMA-OKFREQ-002
- SwRS-OKFSCHEMA-OKFREQ-003
owner: okf-schema maintainers
verification_method: test
verification_criteria: Unit tests over okf_schema.okfreq.core, CliRunner tests
  over the okfreq commands and the repository's own accepted main paths pass;
  the migrated bundle validates with no error, W003 or W004.
documentation_files:
- docs/source/explanation/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-frontmatter.md
- docs/source/reference/okfreq-cli.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
- skills/okfreq-setup/SKILL.md
- src/okf_schema/data/requirements/guidelines/requirements.guidelines.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/README.md
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq.py
- tests/test_okfreq_cli.py
default_owner_email: gaetan@xeberon.net
---

## Measure stakeholder acceptance through declared main paths

### Normative behavior

When a project selects mode linked-swrs-and-acceptance-paths, okfreq SHALL derive stakeholder acceptance from @accepts_req markers naming declared main paths, and SHALL report per-path coverage, findings and report format 2 that the mode defines.

### Scenario S1: Select the acceptance-paths mode

- GIVEN a bundle whose `config.yml` names `strs_test_coverage_mode`
- WHEN the configuration is loaded
- THEN `linked-swrs-and-acceptance-paths` is accepted beside the two existing
  modes, an unsupported value is refused with a message listing the three
  modes, and `okfreq init` writes `markers.accepts` and `accepted_in_files` in
  `generated_fields` while still never replacing an existing bundle.

### Scenario S2: Declare scenarios and waive acceptance

- GIVEN a requirement whose frontmatter declares `scenarios:` as a non-empty
  list of `{id: S<n>, title: …}` mappings
- WHEN the bundle is validated
- THEN the schema refuses an extra key, a malformed id and an empty title in
  every mode, the new mode also refuses duplicate ids, and a whole-StRS
  `acceptance_exemption: true` without a non-blank
  `acceptance_exemption_reason` is refused while both authored fields survive
  `update-coverage` untouched.

### Scenario S3: Read two test verbs and their scenario fragments

- GIVEN test files carrying `@tests_req` and `@accepts_req` markers, some with a
  `#S<n>` fragment
- WHEN the markers are scanned
- THEN each marker is attributed to its configured keyword with its file, line
  and fragment, any other suffix is read as no fragment, an unknown ID lands in
  `missing_ids`, two kinds sharing one keyword is refused, and `okfreq trace`
  prints `accepted: N`.

### Scenario S4: Decide what each marker counts

- GIVEN a targeted requirement that declares `scenarios:` or declares none
- WHEN a `@tests_req` or `@accepts_req` marker targets it
- THEN a fragment naming a declared scenario counts for that scenario, a
  fragmentless marker counts for the whole requirement only when it declares no
  scenario, a missing or undeclared fragment is an error that does not count,
  and `@accepts_req` on a SwRS is refused with the SwRS schema's own text.

### Scenario S5: Compute paths, transitions and coverage

- GIVEN the counting markers of a bundle in the new mode
- WHEN coverage is computed and written
- THEN a StRS reports independent `tested` and `accepted` path counts and is
  `covered` only with its linked SwRS satisfied and either every path accepted
  or a justified whole-StRS waiver, a SwRS that declares transitions is
  test-covered only when each one is marked, and the generated
  `tested_in_files` and `accepted_in_files` list counting markers only.

### Scenario S6: Guide the author with W003 and W004

- GIVEN a live StRS with no declared `scenarios:` or no counting acceptance
  marker
- WHEN the bundle is validated
- THEN `W003` quotes the path or scenario headings it found and gives the
  `scenarios:` block to paste, `W004` asks for an `@accepts_req` marker and
  links the execution-cost guidance, neither changes the exit code, and a
  justified waiver suppresses `W004` only.

### Scenario S7: Report paths and pre-fill scenarios

- GIVEN a bundle in the new mode
- WHEN a report is generated or a requirement is created
- THEN the report has `format_version` 2 with per-StRS path, test and
  acceptance fields, per-SwRS transitions and a Markdown table with `Tested`
  and `Accepted` columns, and `okfreq new` pre-fills `scenarios:` from the
  headings of the body it writes.

### Verification notes

- Method: unit tests of `okf_schema.okfreq.core`, `CliRunner` tests of the
  `okfreq` commands, the installed-wheel acceptance tests of this repository,
  and the repository's own migrated bundle.
- Criteria: the tests pass and `okfreq validate requirements --prose
  --check-links` reports no error, `W003` or `W004`.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
- Depends on:
  - [SwRS-OKFSCHEMA-OKFREQ-002](SwRS-OKFSCHEMA-OKFREQ-002.md): Author and validate requirements
  - [SwRS-OKFSCHEMA-OKFREQ-003](SwRS-OKFSCHEMA-OKFREQ-003.md): Trace requirements to source and tests
<!-- okf:links:end -->

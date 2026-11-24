---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-015
uuid: 15db3020-566d-43a7-87bd-709e12f436d7
title: Trace scenario coverage and stakeholder acceptance
description: The requirements tool SHALL track declared software transitions and
  stakeholder acceptance paths using validated scenario-specific markers and
  report their coverage.
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
verification_criteria: Focused scenario coverage and compatibility tests and the
  complete project preflight pass.
documentation_files:
- docs/source/reference/okfreq-acceptance-paths.md
- docs/source/explanation/okfreq-acceptance-paths.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
- skills/okfreq-setup/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
scenarios:
- id: S1
  title: Scaffold scenario-aware requirements
- id: S2
  title: Validate and trace scenario markers
- id: S3
  title: Generate scenario coverage and reports
- id: S4
  title: Preserve existing modes and protect retirement
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq.py
default_owner_email: gaetan@xeberon.net
---

## Trace scenario coverage and stakeholder acceptance

### Normative behavior

The requirements tool SHALL track declared software transitions and stakeholder acceptance paths using validated scenario-specific markers and report their coverage.

### Scenario: Scaffold scenario-aware requirements

- GIVEN the acceptance-path coverage mode in a requirements bundle
- WHEN a requirement is created
- THEN its frontmatter declares stable scenarios corresponding to its template
  headings, and the schemas accept declared scenarios and acceptance fields.

### Scenario: Validate and trace scenario markers

- GIVEN requirements and configured source and test markers
- WHEN validation and tracing run
- THEN fragments identify declared scenarios, invalid or misplaced markers
  produce findings without counting as evidence, and missing stakeholder paths
  or acceptance evidence are reported as advisory warnings.

### Scenario: Generate scenario coverage and reports

- GIVEN a valid scenario-aware bundle with tests and acceptance markers
- WHEN coverage and reports are generated
- THEN all declared SwRS transitions must be tested, stakeholder paths report
  testing and acceptance separately, and the JSON and Markdown reports expose
  path counts and missing transitions without inventing evidence.

### Scenario: Preserve existing modes and protect retirement

- GIVEN an older coverage mode or a draft requirement named by a marker
- WHEN coverage is computed or retirement is requested
- THEN older modes preserve their coverage semantics and a referenced draft
  cannot be retired until its marker is removed.

### Verification notes

- Method: test.
- Criteria: focused tests exercise the scenarios, reporting and invalid inputs;
  the isolated installed-wheel workflow exercises the user-facing commands.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

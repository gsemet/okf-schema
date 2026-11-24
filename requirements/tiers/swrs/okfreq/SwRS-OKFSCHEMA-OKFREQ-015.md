---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-015
uuid: a533cbe5-cde3-4c79-abcb-d256ae3bc67a
title: Measure StRS acceptance paths
description: The okfreq CLI SHALL validate declared scenarios, classify
  scenario-aware test and acceptance markers, and report independent tested and
  accepted path coverage.
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
  title: Classify scenario-aware markers
- id: S2
  title: Refuse invalid fragments and old schemas
- id: S3
  title: Report independent path and transition coverage
- id: S4
  title: Scaffold and preserve accepted evidence
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq_acceptance_paths.py
default_owner_email: gaetan@xeberon.net
documentation_files:
- docs/source/explanation/okfreq-acceptance-paths.md
- docs/source/reference/okfreq-acceptance-paths.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/tests/test_acceptance_export.py
---

## Measure StRS acceptance paths

### Normative behavior

The okfreq CLI SHALL validate declared scenarios, classify scenario-aware test and acceptance markers, and report independent tested and accepted path coverage.

### Scenario S1: Classify scenario-aware markers

- GIVEN a requirement declares paths or transitions
- WHEN okfreq scans implementation, test, and acceptance markers
- THEN it preserves the marker kind, file, line, and declared `#S<n>` fragment.

### Scenario S2: Refuse invalid fragments and old schemas

- GIVEN a missing or undeclared fragment, acceptance marker on SwRS, or pre-0.18 SwRS schema
- WHEN requirements are validated
- THEN okfreq reports an actionable error and the invalid marker does not count.

### Scenario S3: Report independent path and transition coverage

- GIVEN valid StRS and SwRS scenario markers
- WHEN a report is generated
- THEN tested and accepted path fractions, missing transitions, and waivers are independent and schema-valid.

### Scenario S4: Scaffold and preserve accepted evidence

- GIVEN an acceptance-paths bundle is initialized or coverage is refreshed
- WHEN `okfreq new` or `okfreq update-coverage` writes generated values
- THEN matching scenarios are scaffolded, only configured counting evidence is generated, and old modes retain their output policy.

### Verification notes

<!-- Name the verification method, evidence, and boundaries. Do not claim
     coverage until implementation and test markers exist. -->

- Method: focused unit, CLI, report-schema, and isolated installed-wheel tests.
- Criteria: targeted acceptance-path tests and `just preflight` pass; examples and reports are synchronized.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-004
uuid: 1440832e-5205-4760-9aac-85410670dda0
title: Report requirement health
description: The okfreq layer reports requirement hierarchy, coverage, and
  lifecycle health.
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
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/reference/okfreq-cli.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-frontmatter.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/README.md
default_owner_email: gaetan@xeberon.net
---

## Report requirement health

### Normative behavior

When a user requests requirement health information, `okfreq` SHALL report schema
health, hierarchy errors, implementation and test marker coverage, and lifecycle
counts as separate inspectable metrics.

### Scenario: Generate a machine-readable report

- GIVEN a structurally valid requirements bundle
- WHEN the user generates a JSON report
- THEN the report contains separate schema, graph, coverage, and lifecycle data
  for the current bundle

### Scenario: Report replacement and related requirements

- GIVEN requirements that use `superseded_by` and `relates_to`
- WHEN the graph or the JSON report is produced
- THEN `okfreq graph --json` and each report record list `superseded_by`, the
  computed `supersedes` and `relates_to`, and the published JSON Schema describes them

### Scenario: Report unhealthy requirements

- GIVEN a bundle with a hierarchy error or missing coverage evidence
- WHEN health reporting runs
- THEN the discrepancy appears in its corresponding metric without being hidden
  by a composite score

### Verification notes

- Method: automated tests of status, graph, JSON, and Markdown report output.
- Criteria: report totals match the loaded corpus and known discrepancies appear
  in the correct categories.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

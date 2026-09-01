---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-004
uuid: 1440832e-5205-4760-9aac-85410670dda0
title: Report requirement health
description: The okfreq layer reports requirement hierarchy, coverage, and
  lifecycle health.
project: okf-schema
scope: okfreq
lifecycle: draft
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
---

## EARS Expression

### Normative behavior

When a user requests requirement health information, `okfreq` SHALL report schema
health, hierarchy errors, implementation and test marker coverage, and lifecycle
counts as separate inspectable metrics.

### Scenario: Generate a machine-readable report

- GIVEN a structurally valid requirements bundle
- WHEN the user generates a JSON report
- THEN the report contains separate schema, graph, coverage, and lifecycle data
  for the current bundle

### Scenario: Report unhealthy requirements

- GIVEN a bundle with a hierarchy error or missing coverage evidence
- WHEN health reporting runs
- THEN the discrepancy appears in its corresponding metric without being hidden
  by a composite score

### Verification notes

- Method: automated tests of status, graph, JSON, and Markdown report output.
- Criteria: report totals match the loaded corpus and known discrepancies appear
  in the correct categories.

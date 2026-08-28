---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-005
uuid: 39a0921f-40d9-4fe5-917b-a513715204d4
title: Validate requirement bundles
description: When a requirement bundle is validated, okfreq SHALL check schemas,
  identities, hierarchy links, lifecycle values, and optional EARS prose while
  keeping prose findings advisory.
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

When a requirement bundle is validated, okfreq SHALL check schemas, identities, hierarchy links, lifecycle values, and optional EARS prose while keeping prose findings advisory.

### Scenario: Validate a conforming requirement graph

- GIVEN requirements that satisfy the configured schema, levels, lifecycle, and
  parent hierarchy
- WHEN `okfreq validate` or `okfreq lint` runs
- THEN structural validation succeeds and reports the number of inspected
  requirements

### Scenario: Keep prose guidance advisory

- GIVEN a structurally valid requirement with an incomplete EARS body
- WHEN validation runs with prose checks enabled
- THEN the tool reports a prose warning without changing the successful
  structural-validation exit status

### Verification notes

- Method: unit and CLI tests for schemas, hierarchy failures, and prose warnings.
- Criteria: structural failures exit unsuccessfully, valid graphs succeed, and
  prose-only findings remain warnings.

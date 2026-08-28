---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-006
uuid: f8c69276-bd43-488c-993e-11d6a965301a
title: Merge requirement configuration safely
description: When configuration is imported or merged, okfreq SHALL preserve
  existing conflicting values and unknown keys while reporting every conflict
  for review.
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
- src/okf_schema/okfreq/cli.py
tested_in_files:
- tests/test_okfreq.py
---

## EARS Expression

### Normative behavior

When configuration is imported or merged, okfreq SHALL preserve existing conflicting values and unknown keys while reporting every conflict for review.

### Scenario: Merge compatible configuration

- GIVEN current and imported configurations with distinct keys
- WHEN the user imports or merges the configuration
- THEN missing keys are added and unknown producer metadata is preserved

### Scenario: Preserve an existing conflicting value

- GIVEN current and imported configurations assign different values to the same
  key
- WHEN the merge runs
- THEN the current value remains unchanged and the key path is reported as a
  conflict

### Verification notes

- Method: core and CLI tests using compatible, conflicting, unknown, and malformed
  configuration inputs.
- Criteria: compatible keys merge, conflicts are complete and deterministic, and
  existing values are never silently overwritten.

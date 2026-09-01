---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-001
uuid: 8467b466-1a9a-4ed8-95d1-f097d6253905
title: Provide deterministic knowledge-base operations
description: The okfkb subset provides deterministic knowledge-base operations.
project: okf-schema
scope: okfkb
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFKB-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/okfkb/cli.py
tested_in_files:
- tests/test_kb_cli.py
---

## EARS Expression

### Normative behavior

When a user invokes an `okfkb` command with the same bundle state and arguments,
the CLI SHALL perform the same knowledge-base operation and produce equivalent
structured results.

### Scenario: Repeat a read-only operation

- GIVEN an unchanged knowledge bundle
- WHEN the same `okfkb` query is run more than once
- THEN each invocation returns equivalent ordered results without changing the
  bundle

### Scenario: Reject invalid input

- GIVEN arguments or bundle content that violate the selected command's contract
- WHEN the command is invoked
- THEN the CLI reports an actionable error and does not partially mutate the
  bundle

### Verification notes

- Method: automated CLI tests over fixed knowledge-base fixtures.
- Criteria: repeated operations are stable and failed operations leave authored
  fixture content intact.

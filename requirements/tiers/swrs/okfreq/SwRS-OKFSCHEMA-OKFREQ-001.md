---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-001
uuid: 84d78e43-e518-466d-85a2-f98a3a5b9290
title: Provide requirements traceability operations
description: The okfreq subset provides requirement traceability operations.
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
- src/okf_schema/okfreq/cli.py
tested_in_files:
- tests/test_okfreq.py
---

## EARS Expression

### Normative behavior

When a user invokes an `okfreq` command, the CLI SHALL provide deterministic
creation, validation, inspection, traceability, lifecycle, graph, and reporting
operations against the resolved requirements bundle.

### Scenario: Operate on a resolved bundle

- GIVEN a project containing one uniquely resolvable requirements bundle
- WHEN the user invokes an `okfreq` inspection command from the project or bundle
  path
- THEN the command operates on the bundle that owns `config.yml` and reports a
  stable result

### Scenario: Reject an invalid operation

- GIVEN an unknown requirement identity, invalid hierarchy target, or malformed
  bundle
- WHEN a mutating `okfreq` command is requested
- THEN the CLI exits unsuccessfully with an actionable error and avoids a partial
  write

### Verification notes

- Method: automated command-surface and failure-path tests.
- Criteria: supported commands resolve the same bundle consistently, and rejected
  operations preserve existing files.

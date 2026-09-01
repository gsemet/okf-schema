---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-003
uuid: bcc27c4b-6b64-454b-900e-3e0e5f37d830
title: Capture immutable knowledge findings
description: The okfkb layer records one immutable empirical Finding per capture
  operation.
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
- src/okf_schema/okfkb/finding.py
- src/okf_schema/okfkb/cli.py
tested_in_files:
- tests/test_kb_finding.py
---

## EARS Expression

### Normative behavior

When a user records an empirical observation, the `okfkb` CLI SHALL create one
new immutable Finding containing the supplied observation context and provenance.

### Scenario: Record one finding

- GIVEN a valid knowledge bundle and observation metadata
- WHEN the user invokes the finding-recording command once
- THEN exactly one new Finding document is created with a unique identity and the
  supplied evidence context

### Scenario: Preserve earlier evidence

- GIVEN a bundle containing existing Finding documents
- WHEN another observation is recorded
- THEN the existing Finding documents remain unchanged and the new observation is
  stored as a separate Finding

### Verification notes

- Method: automated tests that compare the bundle before and after captures.
- Criteria: each successful capture adds one valid Finding and does not rewrite
  existing findings.

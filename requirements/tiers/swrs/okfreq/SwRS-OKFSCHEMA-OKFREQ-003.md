---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-003
uuid: ff977cf5-5530-4373-a9d1-63f73394395a
title: Trace requirements to source and tests
description: The okfreq layer records implementation and test markers and
  computes coverage.
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

When traceability is scanned or refreshed, `okfreq` SHALL derive implementation
and test coverage from configured source markers while preserving authored
requirement fields and Markdown bodies.

### Scenario: Resolve valid markers

- GIVEN configured source and test locations containing markers for known SwRS
  identities
- WHEN the user runs trace or coverage update
- THEN each marker is associated with its source-relative file and the generated
  coverage fields reflect those associations

### Scenario: Encounter suspect markers

- GIVEN a marker for an unknown ID, a repeated marker in one file, or a marker on
  a non-leaf requirement
- WHEN traceability is scanned
- THEN `okfreq` reports the discrepancy separately without treating it as valid
  coverage evidence

### Verification notes

- Method: automated marker-scan and generated-update tests.
- Criteria: valid multi-file coverage is retained, suspect references are
  classified correctly, and only configured generated fields change during an
  update.

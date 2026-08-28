---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-006
uuid: 257d6303-2909-4a9d-bab4-fe1b4355bb89
title: Validate OKF 0.2 provenance and lifecycle
description: When OKF 0.2 metadata is validated, okf-schema SHALL enforce
  provenance, verification, lifecycle, resource, trust-tier, and staleness rules
  with actionable findings.
project: okf-schema
scope: core
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/api.py
- src/okf_schema/validator.py
tested_in_files:
- tests/test_api.py
- tests/test_okf2_compliance.py
---

## EARS Expression

### Normative behavior

When OKF 0.2 metadata is validated, okf-schema SHALL enforce provenance, verification, lifecycle, resource, trust-tier, and staleness rules with actionable findings.

### Scenario: Derive trust and staleness

- GIVEN a concept containing OKF 0.2 provenance, verification, and lifecycle
  metadata
- WHEN the concept is validated or inspected
- THEN the tool derives its trust tier and staleness consistently from that
  metadata

### Scenario: Report inconsistent governed metadata

- GIVEN invalid provenance, verification, lifecycle, or resource relationships
- WHEN OKF 0.2 validation runs
- THEN the result contains the corresponding actionable error or warning code
  without altering the concept

### Verification notes

- Method: OKF 0.2 compliance and validator tests.
- Criteria: valid metadata produces the expected trust/staleness result and each
  invalid governed condition produces its documented finding category.

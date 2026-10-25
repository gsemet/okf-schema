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
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
---

## Validate OKF 0.2 provenance and lifecycle

### Normative behavior

When OKF 0.2 metadata is validated, okf-schema SHALL enforce provenance, verification, lifecycle, resource, trust-tier, and staleness rules with actionable findings.

### Scenario: Derive trust and staleness

- GIVEN a concept containing OKF 0.2 provenance, verification, and lifecycle
  metadata
- WHEN the concept is validated or inspected
- THEN the tool derives its trust tier and staleness consistently from that
  metadata

### Scenario: Compare `stale_after` as an instant

- GIVEN a concept whose `stale_after` is an ISO 8601 datetime with an explicit
  UTC offset (`Z` or `±HH:MM`), quoted or as an unquoted YAML timestamp, or a
  bare ISO date
- WHEN the concept is validated or inspected
- THEN it is stale (W11, `stale: true`) once the current UTC instant, or for a
  bare date the current calendar day, has reached that value

### Scenario: Report an unusable `stale_after`

- GIVEN a concept whose `stale_after` is present but is not a bare ISO date or
  a datetime with an explicit UTC offset, such as a typo, a datetime without an
  offset, or a number
- WHEN OKF 0.2 validation runs
- THEN the result contains warning W16 and the concept is not reported stale,
  so the disabled staleness check is visible rather than silent

### Scenario: Report inconsistent governed metadata

- GIVEN invalid provenance, verification, lifecycle, or resource relationships
- WHEN OKF 0.2 validation runs
- THEN the result contains the corresponding actionable error or warning code
  without altering the concept

### Verification notes

- Method: OKF 0.2 compliance and validator tests.
- Criteria: valid metadata produces the expected trust/staleness result and each
  invalid governed condition produces its documented finding category.

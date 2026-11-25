---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-006
uuid: 257d6303-2909-4a9d-bab4-fe1b4355bb89
title: Validate OKF 0.2 provenance and lifecycle
description: When OKF 0.2 metadata is validated or inspected, okf-schema SHALL
  derive its trust tier and staleness and enforce provenance, verification,
  lifecycle, resource, trust-tier, and staleness rules with actionable findings.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-001
depends_on:
- SwRS-OKFSCHEMA-CORE-010
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/api.py
- src/okf_schema/cli.py
- src/okf_schema/validator.py
tested_in_files:
- tests/test_api.py
- tests/test_cli_remaining.py
- tests/test_okf2_compliance.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
scenarios:
- id: S1
  title: Derive trust and staleness
- id: S2
  title: Compare `stale_after` as an instant
- id: S3
  title: Report an unusable `stale_after`
- id: S4
  title: Report inconsistent governed metadata
- id: S5
  title: Count every OKF 0.2 actor form
- id: S6
  title: Print a concept's trust tier and staleness
- id: S7
  title: Refuse to print the trust tier of a missing concept
- id: S8
  title: Refuse to print the trust tier of a file that is not valid UTF-8
default_owner_email: gaetan@xeberon.net
---

## Validate OKF 0.2 provenance and lifecycle

### Normative behavior

When OKF 0.2 metadata is validated or inspected, okf-schema SHALL derive its trust tier and staleness and enforce provenance, verification, lifecycle, resource, trust-tier, and staleness rules with actionable findings.

### Scenario S1: Derive trust and staleness

- GIVEN a concept containing OKF 0.2 provenance, verification, and lifecycle
  metadata
- WHEN the concept is validated or inspected
- THEN the tool derives its trust tier and staleness consistently from that
  metadata

### Scenario S2: Compare `stale_after` as an instant

- GIVEN a concept whose `stale_after` is an ISO 8601 datetime with an explicit
  UTC offset (`Z` or `±HH:MM`), quoted or as an unquoted YAML timestamp, or a
  bare ISO date
- WHEN the concept is validated or inspected
- THEN it is stale (W11 on validation, `stale: true` from `okf-schema trust`,
  `stale` true in the API result, `[STALE]` in `list`) once the current UTC instant,
  or for a bare date the current calendar day, has reached that value

### Scenario S3: Report an unusable `stale_after`

- GIVEN a concept whose `stale_after` is present but is not a bare ISO date or
  a datetime with an explicit UTC offset, such as a typo, a datetime without an
  offset, or a number
- WHEN OKF 0.2 validation runs
- THEN the result contains warning W16 and the concept is not reported stale,
  so the disabled staleness check is visible rather than silent

### Scenario S4: Report inconsistent governed metadata

- GIVEN invalid provenance, verification, lifecycle, or resource relationships
- WHEN OKF 0.2 validation runs
- THEN the result contains the corresponding actionable error or warning code
  without altering the concept

### Scenario S5: Count every OKF 0.2 actor form

- GIVEN a concept whose `verified[].by` actor is written as `{producer}/{version}`,
  `human:<id>`, `process:<id>`, any other `{prefix}:{identifier}`, or in no recognized form
- WHEN the concept is validated or inspected
- THEN a `human:<id>` actor makes it human-reviewed, any other non-empty actor (`human:`
  with no identifier included) makes it machine-confirmed, and only an actor in no
  recognized form raises warning W10

### Scenario S6: Print a concept's trust tier and staleness

- GIVEN a concept in the bundle, with or without a `verified` field (a list or a bare
  mapping) and a `stale_after` value
- WHEN the user runs `okf-schema trust` on it
- THEN standard output is `trust: TIER` with TIER derived from `verified` only
  (`unverified`, `machine-confirmed` or `human-reviewed`), followed by `stale: true`
  only when the concept is stale; the command exits 0 for every tier, including
  `unverified`, prints no score, and writes no file

### Scenario S7: Refuse to print the trust tier of a missing concept

- GIVEN a concept path that names no file in the bundle, with or without `.md`
- WHEN the user runs `okf-schema trust` on it
- THEN the command writes `Error: Concept not found: ...` (the message `show` gives for
  it) to standard error, prints no `trust:` line, exits 2 and writes no file

### Scenario S8: Refuse to print the trust tier of a file that is not valid UTF-8

- GIVEN a concept file in the bundle whose bytes are not valid UTF-8
- WHEN the user runs `okf-schema trust` on it
- THEN the command writes one line, `Error: Concept file is not valid UTF-8: PATH`
  where PATH is the path of the file, to standard error, with no traceback, prints no
  `trust:` line, exits 2 and writes no file

### Verification notes

- Method: OKF 0.2 compliance and validator tests, and CLI tests of the `trust`
  command.
- Criteria: valid metadata produces the expected trust/staleness result and each
  invalid governed condition produces its documented finding category. `trust` prints
  exactly `trust: TIER` and, when stale, `stale: true`, and changes no file; a
  missing concept is refused with exit 2; a file that is not valid UTF-8 is refused
  with one `Error: Concept file is not valid UTF-8: PATH` line and exit 2.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-CORE-001](../../strs/core/StRS-OKFSCHEMA-CORE-001.md): Validate OKF bundle structures
- Depends on:
  - [SwRS-OKFSCHEMA-CORE-010](SwRS-OKFSCHEMA-CORE-010.md): Stay inside the bundle
<!-- okf:links:end -->

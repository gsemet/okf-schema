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

### Scenario: Check evidence links using the base schema contract

- GIVEN a Concept with `derived_from: [findings/cache-run]` and
  `links: [structures/cache.md]`, and corresponding files inside the KB
- WHEN `okfkb validate --check-links` runs
- THEN base API checking resolves the extensionless evidence path as
  `findings/cache-run.md` and the exact link as `structures/cache.md`

### Scenario: Report a missing evidence target without rewriting knowledge

- GIVEN an annotated evidence path whose exact Markdown target is missing
- WHEN KB validation opts into target checks
- THEN it reports `E10` without changing the Finding, derived document, or their values

The shared contract is specified by `SwRS-OKFSCHEMA-CORE-007`. Checks remain off by default;
existing KB schemas and documents are not migrated. Generated `derives_to` references use the same
extensionless bundle-path rule as authored `derived_from` references.

### Verification notes

- Method: automated CLI tests over fixed knowledge-base fixtures.
- Criteria: repeated operations are stable and failed operations leave authored
  fixture content intact.

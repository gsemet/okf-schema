---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-007
uuid: bf73d43a-746b-49f9-816f-a56a03b9c374
title: Manage requirement lifecycle explicitly
description: When a confirmed archive or supersede operation is requested,
  okfreq SHALL apply the lifecycle transition without deleting the requirement
  and SHALL reject unconfirmed or unknown targets.
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

When a confirmed archive or supersede operation is requested, okfreq SHALL apply the lifecycle transition without deleting the requirement and SHALL reject unconfirmed or unknown targets.

### Scenario: Apply a confirmed lifecycle transition

- GIVEN a known requirement and explicit confirmation
- WHEN archive or supersede is requested with a valid replacement where required
- THEN `okfreq` updates the lifecycle metadata while preserving the requirement
  document and stable UUID

### Scenario: Reject an unsafe transition

- GIVEN confirmation is absent or a requirement or replacement target is unknown
- WHEN a lifecycle command is invoked
- THEN the command exits unsuccessfully and leaves every requirement unchanged

### Verification notes

- Method: CLI lifecycle tests comparing files before and after each operation.
- Criteria: confirmed valid transitions preserve content and identity, while all
  rejected transitions perform no writes.

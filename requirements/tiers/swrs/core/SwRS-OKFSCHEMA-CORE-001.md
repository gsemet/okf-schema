---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-001
uuid: 7778d823-a430-4cc8-948c-ae3b3e080da8
title: Validate generic OKF bundles
description: The generic okf-schema layer validates and manages ordinary OKF
  bundles.
project: okf-schema
scope: core
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-001
annotation_exemption: false
exemption_reason: null
derived_by: []
implemented_in_files:
- src/okf_schema/api.py
- src/okf_schema/cli.py
- src/okf_schema/schemas/__init__.py
- src/okf_schema/validator.py
tested_in_files:
- tests/test_api.py
- tests/test_cli_core.py
- tests/test_validator.py
---

## EARS Expression

### Normative behavior

When a user invokes a generic `okf-schema` validation or management command, the
CLI SHALL apply the configured OKF schemas and bundle rules deterministically and
report actionable results without silently changing authored content.

### Scenario: Validate a conforming bundle

- GIVEN an OKF bundle whose documents satisfy their declared schemas
- WHEN the user runs the validation command
- THEN the command reports no validation errors and exits successfully

### Scenario: Reject an invalid document

- GIVEN an OKF document with missing or invalid required metadata
- WHEN the user runs the validation command
- THEN the command identifies the invalid document and exits unsuccessfully

### Scenario: Accept portable bundle contents

- GIVEN an OKF bundle containing conforming concept documents at its root or in
  subdirectories and non-Markdown files referenced as attachments
- WHEN the user runs the validation command
- THEN the concept documents are validated at either location and the
  non-Markdown attachments do not produce document validation errors

### Verification notes

- Method: automated CLI and API tests using valid and invalid bundle fixtures.
- Criteria: results and exit status are deterministic, and validation leaves
  fixture content unchanged.

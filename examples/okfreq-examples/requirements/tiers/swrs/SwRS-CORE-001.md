---
type: SwRS
id: SwRS-CORE-001
uuid: 00000000-0000-4000-8000-000000000002
title: Write CSV output
description: When export is requested, the service SHALL write the report as CSV
  output.
project: OKFREQXMP
scope: Core
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-CORE-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/export.py
tested_in_files:
- tests/test_export.py
---

## EARS Expression

### Normative behavior

When export is requested, the service SHALL write the report as CSV output.

### Scenario: Export selected rows

- GIVEN a report containing selected rows
- WHEN CSV export is requested
- THEN the service returns UTF-8 CSV with one record per selected row

### Scenario: Export an empty selection

- GIVEN a report with no selected rows
- WHEN CSV export is requested
- THEN the service returns an empty CSV document without failing

### Verification notes

<!-- Name the verification method, evidence, and boundaries. Do not claim
     coverage until implementation and test markers exist. -->

- Method: test
- Criteria: Automated tests compare exact CSV output for populated and empty inputs.

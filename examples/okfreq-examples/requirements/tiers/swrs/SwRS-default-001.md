---
type: SwRS
id: SwRS-default-001
uuid: a781661b-513f-41b5-aa87-e9d93f599ee0
title: Write CSV output
description: When export is requested, the service SHALL write the report as CSV
  output.
project: OKFREQXMP
scope: default
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-default-001
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

### Scenario: <nominal behavior>

- GIVEN <precondition and relevant inputs>
- WHEN <trigger or action>
- THEN <single observable, verifiable outcome>

### Scenario: <boundary or failure behavior>

- GIVEN <boundary precondition or failure>
- WHEN <trigger or action>
- THEN <observable recovery, rejection, or boundary outcome>

### Verification notes

<!-- Name the verification method, evidence, and boundaries. Do not claim
     coverage until implementation and test markers exist. -->

- Method: <test, inspection, analysis, or demonstration>
- Criteria: <objective pass condition>

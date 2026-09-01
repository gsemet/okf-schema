---
type: SwRS
id: SwRS-CORE-002
uuid: 00000000-0000-4000-8000-000000000003
title: Format Rust CSV rows
description: When Rust export is requested, the service SHALL return the
  selected row as a newline-terminated CSV record.
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
- src/rust_export.rs
tested_in_files:
- tests/rust_export_test.rs
---

## EARS Expression

### Normative behavior

When Rust export is requested, the service SHALL return the selected row as a newline-terminated CSV record.

### Scenario: Return a Rust CSV row

- GIVEN a Rust report row with two fields
- WHEN Rust CSV export is requested
- THEN the service returns the fields as one newline-terminated CSV record

### Scenario: Export an empty Rust row

- GIVEN a Rust report row with two empty fields
- WHEN Rust CSV export is requested
- THEN the service returns a newline-terminated empty CSV record without failing

### Verification notes

<!-- Name the verification method, evidence, and boundaries. Do not claim
     coverage until implementation and test markers exist. -->

- Method: test
- Criteria: The Rust test compares exact output for populated and empty rows.

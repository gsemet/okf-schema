---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-002
uuid: b2e69880-facf-4ee7-bb06-6bdeb27804af
title: Create bundles and concepts
description: When a user initializes a bundle or creates a concept, okf-schema
  SHALL create the requested structure and metadata without overwriting an
  existing target.
project: okf-schema
scope: core
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-002
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/cli.py
tested_in_files:
- tests/test_cli_core.py
---

## EARS Expression

### Normative behavior

When a user initializes a bundle or creates a concept, okf-schema SHALL create the requested structure and metadata without overwriting an existing target.

### Scenario: Initialize and author content

- GIVEN a target path that does not contain the requested bundle or concept
- WHEN the user runs `okf-schema init` or `okf-schema new`
- THEN the CLI creates valid bundle metadata or a concept document with the
  requested type, title, and relative location

### Scenario: Reject an existing target

- GIVEN the destination bundle or concept already exists
- WHEN the same creation command is requested without an explicit supported
  overwrite mode
- THEN the command exits unsuccessfully and preserves the existing target

### Verification notes

- Method: CLI tests in temporary directories.
- Criteria: created bundles validate, requested metadata is present, and existing
  targets remain byte-for-byte unchanged after rejection.

---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-004
uuid: c40f80b8-ba49-4ee6-998a-6791b4fe67da
title: Navigate knowledge-base evidence
description: The okfkb layer searches, reads, queries, and updates
  knowledge-base evidence.
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
- src/okf_schema/okfkb/navigate.py
- src/okf_schema/okfkb/cli.py
tested_in_files:
- tests/test_kb_navigate.py
---

## EARS Expression

### Normative behavior

When a user navigates an `okfkb` bundle, the CLI SHALL expose deterministic
search, read, query, backlink, and managed-update operations over the bundle's
knowledge and evidence.

### Scenario: Locate matching knowledge

- GIVEN a bundle containing indexed knowledge documents
- WHEN the user searches or queries for a matching term or relationship
- THEN the CLI returns the matching documents in a stable, inspectable form

### Scenario: Query an absent target

- GIVEN a query that matches no known document or relationship
- WHEN the navigation command runs
- THEN the CLI reports an empty or not-found result without modifying the bundle

### Verification notes

- Method: automated navigation tests over a fixed multi-layer bundle.
- Criteria: expected documents and backlinks are returned consistently, and
  read-only navigation leaves the bundle unchanged.

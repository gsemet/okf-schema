---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-006
uuid: 5fa79b7f-e2f1-4c3c-804e-43ee0bcdfe59
title: Materialize reciprocal knowledge derivations
description: When an OKFKB bundle is maintained or validated, the CLI SHALL
  deterministically materialize and verify computed reverse derivation links
  from authored canonical source paths without changing authored derivation
  fields.
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
- src/okf_schema/formatter.py
- src/okf_schema/validator.py
- src/okf_schema/okfkb/derivations.py
tested_in_files:
- tests/test_kb_derivations.py
---

## EARS Expression

### Normative behavior

When an OKFKB bundle is maintained or validated, the CLI SHALL deterministically materialize and verify computed reverse derivation links from authored canonical source paths without changing authored derivation fields.

### Scenario: Materialize reciprocal derivations

- GIVEN an OKFKB bundle whose documents use canonical extensionless
  `derived_from` paths
- WHEN managed lint or `okfkb update` runs
- THEN every document contains the deterministic `derives_to` reflection of
  those authored edges without changing `derived_from`

### Scenario: Detect stale or invalid computed graph data

- GIVEN an OKFKB document with a missing or stale `derives_to` value, or a
  non-canonical `derived_from` source
- WHEN read-only validation runs
- THEN validation reports the graph inconsistency without modifying any file

### Verification notes

<!-- Name the verification method, evidence, and boundaries. Do not claim
     coverage until implementation and test markers exist. -->

- Method: automated lint, validation, and navigation tests over temporary
  multi-layer OKFKB bundles.
- Criteria: reverse edges and ownership comments are deterministic, invalid
  paths are reported, validation is read-only, and derivation traversal reaches
  the expected downstream documents.

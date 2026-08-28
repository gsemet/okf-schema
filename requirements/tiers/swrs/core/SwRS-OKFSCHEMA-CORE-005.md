---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-005
uuid: eb55b7d2-fdc8-41a9-b7b6-917e6ec59017
title: Inspect and query bundle knowledge
description: When a user inspects an OKF bundle, okf-schema SHALL provide
  deterministic list, show, search, graph, backlink, and statistics results
  without modifying the bundle.
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
- src/okf_schema/_internal/utils.py
- src/okf_schema/api.py
- src/okf_schema/cli.py
tested_in_files:
- tests/test_api.py
- tests/test_cli_remaining.py
---

## EARS Expression

### Normative behavior

When a user inspects an OKF bundle, okf-schema SHALL provide deterministic list, show, search, graph, backlink, and statistics results without modifying the bundle.

### Scenario: Inspect matching knowledge

- GIVEN a valid bundle containing concepts and Markdown relationships
- WHEN the user lists, shows, searches, graphs, requests backlinks, or requests
  statistics
- THEN the command returns stable results derived from current bundle content

### Scenario: Reject an invalid inspection target

- GIVEN a missing bundle or concept path
- WHEN an inspection operation targets it
- THEN the operation reports an actionable not-found error without modifying any
  existing content

### Verification notes

- Method: public API and CLI tests for list, show, search, graph, backlinks, and
  statistics operations.
- Criteria: ordering and computed relationships are deterministic, missing targets
  fail explicitly, and fixture content remains unchanged.

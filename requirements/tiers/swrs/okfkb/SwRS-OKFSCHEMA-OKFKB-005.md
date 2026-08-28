---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-005
uuid: 558f9c96-63b1-422c-81bb-2d8b8f8ffc86
title: Consolidate knowledge findings
description: The okfkb layer reviews contradictions and promotes evidence with
  human confirmation.
project: okf-schema
scope: okfkb
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFKB-001
annotation_exemption: false
exemption_reason: null
derived_by: []
implemented_in_files:
- src/okf_schema/data/kb/skills/okfkb-distill/SKILL.md
tested_in_files:
- tests/test_kb_install.py
---

## EARS Expression

### Normative behavior

When accumulated findings are reviewed for consolidation, the `okfkb` gardening
workflow SHALL identify supporting and contradictory evidence and require human
confirmation before promoting a synthesized conclusion.

### Scenario: Propose a supported consolidation

- GIVEN multiple findings that support a reusable conclusion
- WHEN the gardening workflow evaluates them
- THEN it presents the evidence links and a proposed destination knowledge layer
  for human review

### Scenario: Encounter contradictory evidence

- GIVEN findings that do not support one unambiguous conclusion
- WHEN consolidation is attempted
- THEN the workflow reports the contradiction and does not silently promote or
  discard either finding

### Verification notes

- Method: installation tests and inspection of the packaged gardening skill.
- Criteria: the installed workflow preserves evidence, exposes contradictions,
  and makes promotion conditional on explicit confirmation.

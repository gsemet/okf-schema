---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-005
uuid: 558f9c96-63b1-422c-81bb-2d8b8f8ffc86
title: Consolidate knowledge findings
description: When findings are consolidated with okfkb-distill, the workflow
  SHALL expose supporting and contradictory evidence and require human
  confirmation before promotion.
project: okf-schema
scope: okfkb
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFKB-001
annotation_exemption: true
exemption_reason: Consolidation is an interactive workflow of the shipped
  okfkb-distill skill; an agent proposes and a human confirms, so no
  deterministic source or test can exercise its scenarios. The skill's wording
  is checked only by package inspection, and no source or test marker claims
  coverage.
derived_by: []
implemented_in_files:
- skills/okfkb-distill/SKILL.md
tested_in_files: []
owner: okf-schema maintainers
verification_method: package tests and instruction inspection
verification_criteria: The distill skill is shipped unchanged, and instruction
  inspection confirms evidence preservation and explicit promotion confirmation.
agent_skill_files:
- skills/okfkb-distill/SKILL.md
scenarios:
- id: S1
  title: Propose a supported consolidation
- id: S2
  title: Encounter contradictory evidence
default_owner_email: gaetan@xeberon.net
---

## Consolidate knowledge findings

### Normative behavior

When accumulated findings are reviewed for consolidation, the `okfkb-distill`
workflow SHALL identify supporting and contradictory evidence and require human
confirmation before promoting a synthesized conclusion.

### Scenario S1: Propose a supported consolidation

- GIVEN multiple findings that support a reusable conclusion
- WHEN the distill workflow evaluates them
- THEN it presents the evidence links and a proposed destination knowledge layer
  for human review

### Scenario S2: Encounter contradictory evidence

- GIVEN findings that do not support one unambiguous conclusion
- WHEN consolidation is attempted
- THEN the workflow reports the contradiction and does not silently promote or
  discard either finding

### Verification notes

- Method: installation tests and inspection of the packaged distill skill.
- Criteria: the installed workflow preserves evidence, exposes contradictions,
  and makes promotion conditional on explicit confirmation.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFKB-001](../../strs/okfkb/StRS-OKFSCHEMA-OKFKB-001.md): Maintain trustworthy engineering knowledge
<!-- okf:links:end -->

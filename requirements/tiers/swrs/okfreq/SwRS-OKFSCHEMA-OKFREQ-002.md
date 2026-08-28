---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-002
uuid: 748d8368-376f-4e23-8f20-ff1d47620135
title: Author and validate requirements
description: The okfreq layer creates, validates, and manages requirement
  documents and lifecycle.
project: okf-schema
scope: okfreq
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason: null
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
- src/okf_schema/data/requirements/guidelines/requirements.guidelines.md
tested_in_files:
- tests/test_okfreq.py
---

## EARS Expression

### Normative behavior

When a user creates a native requirement, `okfreq` SHALL allocate a collision-safe
configured ID and UUID, validate its hierarchy, and write the tier-specific StRS
or SwRS authoring format without changing existing requirements.

### Scenario: Create a stakeholder requirement

- GIVEN a configured StRS level and scope
- WHEN the user runs `okfreq new strs` with normative behavior and stakeholder
  need
- THEN the CLI creates an StRS document containing an EARS expression, preserved
  user need, and a prompted rationale-and-constraints section
- AND when stakeholder need is omitted, the document retains a visible authoring
  placeholder instead of duplicating or inventing stakeholder intent

### Scenario: Create a software requirement

- GIVEN a configured SwRS level and a valid StRS parent
- WHEN the user runs `okfreq new swrs` with normative behavior and the parent ID
- THEN the CLI creates an SwRS document containing the parent link, normative EARS
  behavior, nominal and boundary scenarios, and verification prompts
- AND the CLI rejects a stakeholder `user_need` supplied to the SwRS tier

### Verification notes

- Method: automated creation tests for both tiers, hierarchy failures, and ID
  allocation collisions.
- Criteria: each created document validates, StRS and SwRS bodies use distinct
  formats, missing StRS intent remains explicit, tier-inappropriate fields are
  rejected, and failed creation leaves existing documents unchanged.

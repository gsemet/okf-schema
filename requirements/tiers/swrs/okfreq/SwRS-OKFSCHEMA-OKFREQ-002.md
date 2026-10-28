---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-002
uuid: 748d8368-376f-4e23-8f20-ff1d47620135
title: Author and validate requirements
description: The okfreq layer creates, validates, and manages requirement
  documents and lifecycle.
project: okf-schema
scope: okfreq
lifecycle: proposed
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/data/requirements/guidelines/requirements.guidelines.md
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/reference/okfreq-cli.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-frontmatter.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/README.md
default_owner_email: gaetan@xeberon.net
---

## Author and validate requirements

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

### Scenario: Identify a requirement when reading its body

- GIVEN a requirement title supplied during StRS or SwRS creation
- WHEN the scaffold is generated
- THEN the first Markdown heading repeats the frontmatter title verbatim,
  rather than using a generic EARS label

### Scenario: Never reuse a requirement number

- GIVEN requirements of a level and scope whose highest number is N, or a retired ID
  with a higher number recorded in `retired_ids`
- WHEN a requirement file is deleted and the user runs `okfreq new` for that level and scope
- THEN the new ID uses one more than the highest number among existing and retired IDs,
  so a number freed by deletion is never handed out again

### Verification notes

- Method: automated creation tests for both tiers, hierarchy failures, and ID
  allocation collisions and allocation after a deletion.
- Criteria: each created document validates, StRS and SwRS bodies use distinct
  formats, missing StRS intent remains explicit, tier-inappropriate fields are
  rejected, and failed creation leaves existing documents unchanged.

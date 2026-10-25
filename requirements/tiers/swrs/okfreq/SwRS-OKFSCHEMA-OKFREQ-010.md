---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-010
uuid: 83273861-bf92-4ee8-95cf-25d569fb586e
title: Set up a project's requirements baseline from one skill
description: When a user asks to set up okfreq in a project without a
  requirements bundle, the okfreq-setup skill SHALL direct the agent to deliver
  one pull request that specifies the project's current behaviour, anchored to
  its code and tests, without asking the user.
project: okf-schema
scope: okfreq
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
depends_on:
- SwRS-OKFSCHEMA-OKFREQ-002
- SwRS-OKFSCHEMA-OKFREQ-008
owner: okf-schema maintainers
verification_method: test
verification_criteria: The installed okfreq-setup skill ships with the okfreq
  family, resolves its links inside the installation, and states its stop rules,
  fixed defaults and delivery steps.
documentation_files:
- docs/source/how-to/okfreq-build-requirement-base.md
- docs/source/tutorials/okfreq-traceability.md
agent_skill_files:
- skills/okfreq-setup/SKILL.md
- skills/okfreq/SKILL.md
derived_by: []
implemented_in_files:
- skills/okfreq-setup/SKILL.md
tested_in_files:
- tests/test_skill_resources.py
---

## Set up a project's requirements baseline from one skill

### Normative behavior

When a user asks to set up okfreq in a project without a requirements bundle, the okfreq-setup skill SHALL direct the agent to deliver one pull request that specifies the project's current behaviour, anchored to its code and tests, without asking the user.

### Scenario: Set up a project that has no bundle

- GIVEN a git project with no requirements bundle and an installed `okfreq-setup`
  skill
- WHEN the user asks the agent to set up okfreq
- THEN the skill directs the agent to install okfreq, initialise the bundle,
  write the StRS and SwRS from the code, add implementation and test markers,
  close test gaps and open one pull request, without asking the user anything

### Scenario: Refuse to set up over an existing bundle

- GIVEN a project that already has a requirements `config.yml`
- WHEN the user asks the agent to set up okfreq
- THEN the skill directs the agent to stop and report that `okfreq-gardening`
  applies instead

### Scenario: Stop outside a usable git repository

- GIVEN a directory that is not a git repository or whose default branch cannot
  be determined
- WHEN the user asks the agent to set up okfreq
- THEN the skill directs the agent to stop and report, and never to modify
  changes that were in the worktree before it started

### Verification notes

- Method: automated test that the okfreq family installs `okfreq-setup`, that
  its relative links resolve inside the installation, and that the skill states
  its stop rules and delivery steps.
- Criteria: the test passes; the skill's behaviour with a real agent is not
  verified by this test.

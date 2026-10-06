---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-008
uuid: dd435774-c996-4907-88c0-3bb7350a1bc2
title: Ship usable standalone requirements guidance
description: When requirements guidance is installed, the okfreq distribution
  SHALL provide self-contained operating instructions and executable examples of
  authoring, evidence, reports, navigation and recovery.
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
- SwRS-OKFSCHEMA-OKFREQ-004
- SwRS-OKFSCHEMA-OKFREQ-005
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/reference/okfreq-cli.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-frontmatter.md
- docs/source/tutorials/okfreq-traceability.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/README.md
derived_by: []
implemented_in_files:
- skills/okfreq/SKILL.md
- skills/okfreq-gardening/SKILL.md
- examples/okfreq-examples/showcase.py
tested_in_files:
- tests/test_examples.py
- tests/test_skill_resources.py
- tests/test_tutorial_okfreq.py
---

## Ship usable standalone requirements guidance

### Normative behavior

When requirements guidance is installed, the okfreq distribution SHALL provide
self-contained operating instructions and executable examples of authoring,
evidence, reports, navigation and recovery.

### Scenario: Operate without the tool source checkout

- GIVEN an installed okfreq skill family, the CLI and a target project
- WHEN an agent follows the bundled operations reference
- THEN it can resolve the bundle, author StRS/SwRS, configure scopes and markers,
  inspect links, update evidence and generate reports without this tool's code
  or documentation site

### Scenario: Diagnose incomplete evidence and invalid documents

- GIVEN a missing ID, unavailable root, ambiguous target or incomplete markers
- WHEN the agent inspects CLI findings and the packaged recovery instructions
- THEN it can distinguish a structural error, skipped check and coverage gap
  without inventing evidence or claiming test execution

### Scenario: Run the shipping-manifest demonstration safely

- GIVEN an empty disposable project
- WHEN the executable showcase exercises configuration, markers, file links,
  reports, exemptions and lifecycle transitions
- THEN every scenario verifies its output and preserves the live project bundle

### Scenario: Follow the adoption tutorial without inferred project setup

- GIVEN the tutorial snippets and an installed compatible CLI/test environment
- WHEN the existing CSV feature is backfilled and its contract extended
- THEN the documented implementation/tests, requirement bodies, marker updates,
  harness recipes and report commands run in a disposable project
- AND the examples preserve draft lifecycle states and distinguish declared links
  from the actual test results

### Verification notes

- Method: isolated wheel installation, local reference resolution and executable
  showcase acceptance tests and execution of the actual tutorial snippets.
- Criteria: all packaged references resolve without repository docs/source,
  reports validate against their JSON Schema, invalid documents fail, and
  lifecycle demonstrations preserve stable identity and bodies.

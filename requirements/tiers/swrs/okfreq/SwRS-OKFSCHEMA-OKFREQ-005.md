---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-005
uuid: 39a0921f-40d9-4fe5-917b-a513715204d4
title: Validate requirement bundles
description: When a requirement bundle is validated, okfreq SHALL check schemas,
  identities, hierarchy links, lifecycle values, and optional EARS prose while
  keeping prose findings advisory.
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
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_file_links.py
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

## Validate requirement bundles

### Normative behavior

When a requirement bundle is validated, okfreq SHALL check schemas, identities, hierarchy links, lifecycle values, and optional EARS prose while keeping prose findings advisory.

### Scenario: Validate a conforming requirement graph

- GIVEN requirements that satisfy the configured schema, tiers, lifecycle, and
  parent hierarchy
- WHEN `okfreq validate` or `okfreq lint` runs
- THEN structural validation succeeds and reports the number of inspected
  requirements

### Scenario: Refuse to omit an invalid document

- GIVEN a non-reserved requirement with absent or malformed mapping frontmatter,
  or a missing non-empty string ID
- WHEN validation, indexing, coverage generation or reporting is requested
- THEN the operation fails with the document path instead of silently omitting
  the requirement from counts or generating a misleading report

### Scenario: Keep prose guidance advisory

- GIVEN a structurally valid requirement with an incomplete EARS body
- WHEN validation runs with prose checks enabled
- THEN the tool reports a prose warning without changing the successful
  structural-validation exit status

### Scenario: Check requirement navigation and implementation evidence

- GIVEN annotated `derives_from`, `derived_by`, or `depends_on` requirement IDs with matching
  Markdown basenames, and project-relative `implemented_in_files`/`tested_in_files` paths
- WHEN `okfreq validate` or `okfreq lint` runs with `--check-links --project-root .`
- THEN the base file-link API checks targets using filename-stem and project-relative semantics
  while the requirement graph continues to validate frontmatter IDs independently

### Scenario: Keep target checks explicitly opt-in

- GIVEN an existing requirements bundle whose local schemas may not contain annotations
- WHEN validation runs without `--check-links`
- THEN existing schema and graph validation remains unchanged, without migrating the bundle

Missing exact files and missing or ambiguous stems report `E10`; unavailable roots or inaccessible
candidates report `W15` skips. External tracker IDs remain ordinary strings. The shared resolution
contract belongs to `SwRS-OKFSCHEMA-CORE-007`, not to a separate requirements implementation.

### Verification notes

- Method: unit and CLI tests for schemas, hierarchy failures, and prose warnings.
- Criteria: structural failures exit unsuccessfully, valid graphs succeed, and
  prose-only findings remain warnings.

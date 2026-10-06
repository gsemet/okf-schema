---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-009
uuid: 35379278-8073-45da-8c9a-f6772fd1015f
title: Maintain generated requirement navigation
description: When requirement linting succeeds, okfreq SHALL refresh navigation
  indexes throughout the tiers tree while preserving authored text and change
  history.
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
- SwRS-OKFSCHEMA-OKFREQ-005
owner: okf-schema maintainers
verification_method: test
verification_criteria: Nested indexes are generated idempotently, preview modes
  write nothing, and malformed inputs leave authored text and logs unchanged.
documentation_files:
- docs/source/reference/okfreq-cli.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- src/okf_schema/data/requirements/guidelines/requirements.guidelines.md
example_files:
- examples/okfreq-examples/showcase.py
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/navigation.py
tested_in_files:
- tests/test_requirement_indexes.py
---

## Maintain generated requirement navigation

### Normative behavior

When requirement linting succeeds, okfreq SHALL refresh navigation indexes
throughout the tiers tree while preserving authored text and change history.

### Scenario: Discover requirements through scope indexes

- GIVEN configured tiers and requirements stored in nested scope directories
- WHEN `okfreq lint` succeeds
- THEN the tiers root, each configured tier and every requirement ancestor
  directory contain an index linking their children and listing local requirements
  by ID, title and description

### Scenario: Preserve authored guidance and history

- GIVEN existing frontmatter, introductions, authored text after an index block
  and entries in `tiers/log.md`
- WHEN navigation is refreshed
- THEN only the marked generated block changes, while outside text, the optional
  bundle-root overview and authored history remain unchanged

### Scenario: Preview drift or reject unsafe input

- GIVEN missing/stale indexes, invalid requirement metadata or malformed delimiters
- WHEN lint runs with `--check` or `--diff`, or validation fails
- THEN preview modes write nothing, check mode reports drift with a failing exit,
  and invalid input prevents partial index regeneration

### Verification notes

- Method: CLI and generator regression tests, plus the project's own index-freshness check.
- Criteria: all ancestor links resolve, repeated generation is a no-op, previews
  preserve bytes, and authored content/logs survive updates unchanged.

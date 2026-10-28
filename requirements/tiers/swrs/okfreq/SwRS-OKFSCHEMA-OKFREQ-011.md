---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-011
uuid: 56a96f9f-d18e-4705-a542-0d49f4a26dd1
title: Retire a draft requirement permanently
description: When a confirmed retire operation targets an unreferenced draft
  requirement, okfreq SHALL delete the requirement, record its ID as retired,
  and SHALL NOT allocate that number again.
project: okf-schema
scope: okfreq
lifecycle: proposed
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
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
- src/okf_schema/data/requirements/guidelines/requirements.guidelines.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/README.md
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_examples.py
- tests/test_okfreq.py
default_owner_email: gaetan@xeberon.net
---

## Retire a draft requirement permanently

### Normative behavior

When a confirmed retire operation targets an unreferenced draft requirement, okfreq SHALL delete the requirement, record its ID as retired, and SHALL NOT allocate that number again.

### Scenario: Retire a draft

- GIVEN a draft requirement that no other requirement or source or test marker references
- WHEN the user runs `okfreq retire <ID> --yes`
- THEN the requirement file is deleted, the ID is added to `retired_ids` in `config.yml`,
  and an entry naming the ID is appended to the tier `log.md`
- AND `okfreq new` allocates the next number after the highest number ever used in that
  level prefix and scope, counting existing requirements and retired IDs

### Scenario: Refuse an unsafe retirement

- GIVEN confirmation is absent, the ID is unknown, the requirement is not a draft, another
  requirement derives from, depends on or is superseded by it, or a marker references it
- WHEN the user runs `okfreq retire`
- THEN the command exits unsuccessfully, names the reason, and changes no file

### Scenario: Detect a reused retired ID

- GIVEN a requirement document whose ID is listed in `retired_ids`
- WHEN the bundle is validated
- THEN validation reports an error naming the file and the retired ID

### Verification notes

- Method: automated tests of retirement, refusals, allocation after a deletion and
  validation of a retired ID.
- Criteria: a retired or deleted number is never allocated again, and every refused
  retirement leaves requirements, configuration and log unchanged.

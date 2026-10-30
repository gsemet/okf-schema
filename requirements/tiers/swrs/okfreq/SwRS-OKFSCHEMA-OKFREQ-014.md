---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-014
uuid: 05fb4e2e-8f40-4f70-b6e2-fdc71abae21a
title: Keep requirement bundles native OKF bundles
description: When requirements are created, changed, regenerated or validated,
  okfreq SHALL project the lifecycle onto OKF status, the owner approval onto a
  human verified event and the relation fields onto a generated Links section as
  declared by the bundle schemas, and SHALL run the base OKF checks on the tiers
  folder.
project: okf-schema
scope: okfreq
req_lifecycle: proposed
status: stable
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
- docs/source/reference/okfreq-frontmatter.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-cli.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
example_files:
- examples/okfreq-examples/showcase.py
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_examples.py
- tests/test_okfreq_projection.py
default_owner_email: gaetan@xeberon.net
---

## Keep requirement bundles native OKF bundles

### Normative behavior

When requirements are created, changed, regenerated or validated, okfreq SHALL project the lifecycle onto OKF status, the owner approval onto a human verified event and the relation fields onto a generated Links section as declared by the bundle schemas, and SHALL run the base OKF checks on the tiers folder.

### Scenario: Generate the OKF fields

- GIVEN a bundle created by `okfreq init`, whose `req_lifecycle` property carries
  `x-okf-status-projection` and whose relation fields carry `link-projection`
- WHEN `okfreq new`, `archive`, `supersede`, `update-coverage` or `lint` runs
- THEN each requirement carries the mapped `status` (`draft`, `stable` or
  `deprecated`), a requirement with `approved_by` and `approved_at` carries a
  `verified` event whose `by` is `human:` followed by `approved_by` and whose `at`
  is `approved_at`, and a Links section
  links every resolved relation; `status` and `verified` are generated only when
  listed in `generated_fields`

### Scenario: Report what a plain OKF consumer would misread

- GIVEN a `status` that disagrees with the lifecycle, an `approved_at` that is not
  an ISO 8601 datetime with an offset, a `link-projection` on a resolution that
  leaves the bundle or a status mapping that misses a lifecycle value
- WHEN `okfreq validate` runs
- THEN each is reported as an error; base OKF errors and warnings of the tiers
  folder (for example `E6` or the `log.md` headings `W5` and `W18`) are reported
  too, except the recommendations requirement bundles cover otherwise (`W3`,
  `W4`, `W7`)

### Scenario: Detect a stale projection

- GIVEN a Links section, `status` or `verified` that no longer matches the frontmatter
- WHEN `okfreq lint --check` or `okfreq update-coverage --check` runs
- THEN the command exits non-zero without writing; `lint --check` also fails on a
  `log.md` heading that is not exactly `## YYYY-MM-DD`, newest first

### Verification notes

- Method: test
- Criteria: `tests/test_okfreq_projection.py` and the showcase cover generation,
  lifecycle commands, approval trust, validation findings and the `--check` gates.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->

---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-012
uuid: 816e91ea-6877-46aa-ba48-6288f5a5db50
title: Relate requirements by supersession and association
description: When a requirement is superseded or related to others, okfreq SHALL
  record the replacing requirements in an authored superseded_by list, compute
  the inverse supersedes list, accept an authored relates_to list, and reject
  inconsistent or cyclic references.
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
relates_to:
- SwRS-OKFSCHEMA-OKFREQ-007
- SwRS-OKFSCHEMA-OKFREQ-011
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

## Relate requirements by supersession and association

### Normative behavior

When a requirement is superseded or related to others, okfreq SHALL record the replacing requirements in an authored superseded_by list, compute the inverse supersedes list, accept an authored relates_to list, and reject inconsistent or cyclic references.

### Scenario: Record several replacements

- GIVEN known requirements A, B and C
- WHEN `okfreq supersede A B C --yes` runs
- THEN A has `lifecycle: superseded` and `superseded_by: [B, C]`, its body and UUID
  are unchanged, and a previous `superseded_by` (a list, or the legacy single ID) is
  replaced; a single replacement is written as a one-item list

### Scenario: Compute the inverse supersedes list

- GIVEN `supersedes` is listed in `generated_fields`
- WHEN `okfreq update-coverage` runs
- THEN B and C list A in `supersedes` (sorted), `--check` fails while those values are
  stale, and a requirement that replaces nothing gains no `supersedes` line

### Scenario: Require a replacement for a superseded requirement

- GIVEN a requirement with `lifecycle: superseded` and no `superseded_by`, or a
  `superseded_by` on a requirement that is not superseded
- WHEN `okfreq validate` or `okfreq lint` runs
- THEN validation fails naming the file and the missing or misplaced field

### Scenario: Reject unsafe replacement references

- GIVEN a `superseded_by` or `relates_to` target that is unknown, repeated or the
  requirement itself, a `superseded_by` cycle, or a field that is not a list of IDs
- WHEN `okfreq validate`, `okfreq lint` or `okfreq supersede` runs
- THEN the command fails naming the problem, and `okfreq supersede` writes nothing

### Scenario: Keep the legacy single replacement readable

- GIVEN a requirement written by an earlier release with `superseded_by: ID`
- WHEN validation, the graph, reports or `okfreq retire` read it
- THEN it is treated as a one-item list; validation passes and adds the informational
  finding `I2` suggesting the list form, and nothing is rewritten

### Scenario: Relate requirements laterally

- GIVEN a requirement with `relates_to: [X]` where X exists
- WHEN validation, `okfreq graph --json` or `okfreq generate-report` runs
- THEN the link is reported as authored, no inverse is generated, it carries no
  derivation or coverage meaning, and `okfreq retire` refuses to delete X while it
  is referenced

### Verification notes

- Method: unit and CLI tests for the list and legacy forms, generated `supersedes`,
  validation errors, cycles, retirement and the report; the executable showcase.
- Criteria: valid relations pass, every refusal exits unsuccessfully without writes,
  and generated `supersedes` converges with `update-coverage --check`.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
- Relates to:
  - [SwRS-OKFSCHEMA-OKFREQ-007](SwRS-OKFSCHEMA-OKFREQ-007.md): Manage requirement lifecycle explicitly
  - [SwRS-OKFSCHEMA-OKFREQ-011](SwRS-OKFSCHEMA-OKFREQ-011.md): Retire a draft requirement permanently
<!-- okf:links:end -->

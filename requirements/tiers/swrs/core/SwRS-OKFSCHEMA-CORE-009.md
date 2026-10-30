---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-009
uuid: d8456086-d377-4231-80fe-169c2288fb9d
title: Project schema-declared metadata for plain OKF consumers
description: When a bundle is linted, okf-schema SHALL generate, from the
  link-projection labels and x-okf-status-projection mappings of its schemas, a
  delimited Links section of Markdown links and the OKF status of each document,
  and SHALL report malformed projection annotations and log.md headings that are
  not exactly YYYY-MM-DD, newest first.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-002
annotation_exemption: false
exemption_reason:
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/how-to/write-custom-schema.md
- docs/source/reference/cli.md
- docs/source/reference/validation-codes.md
agent_skill_files:
- skills/okf-schema/SKILL.md
example_files:
- examples/okfkb-hw-knowledge-base/_schema/Base.schema.yaml
derived_by: []
implemented_in_files:
- src/okf_schema/projection.py
- src/okf_schema/validator.py
tested_in_files:
- tests/test_projection.py
default_owner_email: gaetan@xeberon.net
---

## Project schema-declared metadata for plain OKF consumers

### Normative behavior

When a bundle is linted, okf-schema SHALL generate, from the link-projection labels and x-okf-status-projection mappings of its schemas, a delimited Links section of Markdown links and the OKF status of each document, and SHALL report malformed projection annotations and log.md headings that are not exactly YYYY-MM-DD, newest first.

### Scenario: Generate the Links section and status from the schemas

- GIVEN a bundle schema whose relation fields carry an `x-okf-link` with a
  `link-projection` label and whose lifecycle property carries an
  `x-okf-status-projection` mapping
- WHEN `okf-schema lint` or `okfkb update` runs (`--link-projection` is the default)
- THEN each document gets `status` from the mapping, and one delimited
  `### Links` section at the end of its body, with one group per annotated
  field in schema order (base schema first) and one relative link per value with
  the target title; a value that does not resolve stays as code; `--check`
  fails on a stale section

### Scenario: Follow the annotations, not hard-coded names

- GIVEN documents that already carry a generated Links section
- WHEN a `link-projection` label is renamed or removed from the schema and lint runs
- THEN the group is renamed or removed in every document; a section without any
  group is removed, and the `lint --links` body scan ignores the section

### Scenario: Reject malformed annotations and log headings

- GIVEN a `link-projection` that is empty or uses a resolution outside the bundle
  (`project-relative`, `document-relative`), a status mapping to a value outside
  `draft | stable | deprecated` or missing an `enum` value, or a `log.md` heading
  such as `## 2026-10-25 (topic)` or dates out of newest-first order
- WHEN `okf-schema validate` or `okf-schema lint --check` runs
- THEN validation reports `E11` (and `E10` from `--check-links`) for the
  annotation, `W5` or `W18` for the heading, and `lint --check` exits non-zero;
  an incomplete or repeated generated section is refused without writing

### Verification notes

- Method: test
- Criteria: `tests/test_projection.py` covers generation, ordering, renaming,
  removal, unresolved values, malformed sections and annotations, the link-graph
  exclusion, the log heading checks and the okfkb derivation projection.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-CORE-002](../../strs/core/StRS-OKFSCHEMA-CORE-002.md): Maintain and inspect OKF bundles
<!-- okf:links:end -->

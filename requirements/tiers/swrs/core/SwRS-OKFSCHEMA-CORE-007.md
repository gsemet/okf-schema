---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-007
uuid: f50ada10-efe1-4b7b-83ec-0b0c759dba5c
title: Interpret and optionally check schema-declared file references
description: When annotated file targets are explicitly checked, the base
  okf-schema API SHALL resolve applicable x-okf-link string annotations and
  report invalid or skipped targets without modifying document values.
project: okf-schema
scope: core
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-003
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/file_links.py
tested_in_files:
- tests/test_file_links.py
---

## EARS Expression

### Normative behavior

When annotated file targets are explicitly checked, the base `okf-schema` API SHALL resolve
applicable `x-okf-link` string annotations and report invalid or skipped targets without modifying
document values.

### Scenario: Resolve scalar and list references through the shared API

- GIVEN a string property or array string `items` schema annotated with `resolution` and `syntax`
- WHEN a consumer calls `okf_schema.api.check_file_links` or enables `check_links` on base validation
- THEN the shared checker resolves the target using document-relative, bundle-relative,
  project-relative, filename-stem, or bundle-relative-stem semantics independently of plain or
  wikilink syntax

### Scenario: Reject invalid targets and identify checks that cannot run

- GIVEN a missing exact target, malformed annotation, ambiguous basename, rooted escape, or
  unavailable root
- WHEN file-target checking runs
- THEN invalid targets produce `E10` and unavailable roots or unresolved basename searches produce
  explicit `W15` skips, without rewriting frontmatter or claiming that skipped targets exist

### Scenario: Preserve ordinary validation and existing bundles

- GIVEN an existing bundle, including schemas without file-link annotations
- WHEN ordinary validation runs without opting into target checking
- THEN validation behavior and authored values remain unchanged, with no schema migration

### Resolution contract

- Exact relative modes retain file extensions; project roots use explicit input then the containing
  Git root, never a working-directory or editor-workspace fallback.
- `filename-stem` searches case-sensitive Markdown basenames inside the known bundle without ID
  fallback; duplicate basenames are errors.
- `bundle-relative-stem` appends `.md` to one exact bundle path, preserving directories and dots.
- Wikilink labels and heading/block fragments are excluded from the target; fragment existence is
  not checked.
- Bundle/project targets must stay within their roots, including through symlinks.
- New generic default schemas annotate `links` and `backlinks` string items as exact bundle paths.

### Verification notes

- Method: shared API, generic scaffold, and CLI regression tests in `tests/test_file_links.py`.
- Criteria: scalar/list and composition cases resolve deterministically, invalid targets report
  `E10`, unavailable context reports `W15`, and default validation does not change.
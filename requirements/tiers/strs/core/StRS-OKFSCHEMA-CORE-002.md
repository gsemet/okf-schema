---
type: StRS
id: StRS-OKFSCHEMA-CORE-002
uuid: f257e232-c85f-49f5-8f4a-748b0a25005f
title: Maintain and inspect OKF bundles
description: The okf-schema capability SHALL enable maintainers to author,
  normalize, navigate, and evolve OKF bundles without losing authored knowledge.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Maintainers need one deterministic toolchain for creating,
  formatting, indexing, inspecting, and evolving OKF bundles while preserving
  human-authored content and provenance.
derived_by:
- SwRS-OKFSCHEMA-CORE-002
- SwRS-OKFSCHEMA-CORE-003
- SwRS-OKFSCHEMA-CORE-004
- SwRS-OKFSCHEMA-CORE-005
- SwRS-OKFSCHEMA-CORE-009
default_owner_email: gaetan@xeberon.net
---

## Maintain and inspect OKF bundles

### Normative behavior

The okf-schema capability SHALL enable maintainers to author, normalize, navigate, and evolve OKF bundles without losing authored knowledge.

### Preserved stakeholder intent

## User Need

Maintainers need one deterministic toolchain for creating, formatting, indexing, inspecting, and evolving OKF bundles while preserving human-authored content and provenance.

### Rationale and constraints

- Authored Markdown, YAML comments, unknown metadata, and stable concept identity
  must survive maintenance operations.
- Read-only inspection must not mutate the bundle.
- Preview modes must expose proposed changes before write operations are applied.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-OKFSCHEMA-CORE-002](../../swrs/core/SwRS-OKFSCHEMA-CORE-002.md): Create bundles and concepts
  - [SwRS-OKFSCHEMA-CORE-003](../../swrs/core/SwRS-OKFSCHEMA-CORE-003.md): Normalize bundle formatting
  - [SwRS-OKFSCHEMA-CORE-004](../../swrs/core/SwRS-OKFSCHEMA-CORE-004.md): Maintain indexes and superseded links
  - [SwRS-OKFSCHEMA-CORE-005](../../swrs/core/SwRS-OKFSCHEMA-CORE-005.md): Inspect and query bundle knowledge
  - [SwRS-OKFSCHEMA-CORE-009](../../swrs/core/SwRS-OKFSCHEMA-CORE-009.md): Project schema-declared metadata for plain OKF consumers
<!-- okf:links:end -->

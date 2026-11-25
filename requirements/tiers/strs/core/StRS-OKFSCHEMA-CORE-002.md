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
scenarios:
- id: S1
  title: Create a bundle and author a concept
- id: S2
  title: Normalize and index a bundle
- id: S3
  title: Inspect bundle knowledge read-only
derived_by:
- SwRS-OKFSCHEMA-CORE-002
- SwRS-OKFSCHEMA-CORE-003
- SwRS-OKFSCHEMA-CORE-004
- SwRS-OKFSCHEMA-CORE-005
- SwRS-OKFSCHEMA-CORE-009
default_owner_email: gaetan@xeberon.net
tested_in_files:
- tests/test_integration.py
accepted_in_files:
- tests/test_acceptance_core.py
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

### Main paths

#### Path S1: Create a bundle and author a concept

1. A maintainer initializes a new OKF bundle and creates a concept document via `okf-schema`.
2. The CLI scaffolds the bundle and writes the concept document with valid frontmatter.
3. The resulting bundle validates cleanly with `okf-schema validate`.

#### Path S2: Normalize and index a bundle

1. A maintainer has an OKF bundle whose frontmatter or navigation indexes need updating.
2. The maintainer runs `okf-schema format` and `okf-schema index` (or `lint`).
3. Frontmatter formatting and generated index blocks are normalized while preserving authored Markdown content.

#### Path S3: Inspect bundle knowledge read-only

1. A maintainer has an existing OKF bundle with linked concepts.
2. The maintainer runs read-only inspection commands (`list`, `stats`, `backlinks`).
3. The commands report the bundle's concepts, statistics, and backlinks without modifying any bundle file.

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

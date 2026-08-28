---
type: StRS
id: StRS-OKFSCHEMA-CORE-002
uuid: f257e232-c85f-49f5-8f4a-748b0a25005f
title: Maintain and inspect OKF bundles
description: The okf-schema capability SHALL enable maintainers to author,
  normalize, navigate, and evolve OKF bundles without losing authored knowledge.
project: okf-schema
scope: core
lifecycle: draft
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
---

## EARS Expression

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

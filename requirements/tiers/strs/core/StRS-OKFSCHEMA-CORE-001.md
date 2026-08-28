---
type: StRS
id: StRS-OKFSCHEMA-CORE-001
uuid: 7d6546eb-9bea-482c-9660-9f031d49970b
title: Validate OKF bundle structures
description: The generic CLI validates OKF bundle structure and schemas.
project: okf-schema
scope: core
lifecycle: draft
origin: native
tier: StRS
derives_from: []
user_need: Teams need deterministic validation of ordinary OKF bundles.
derived_by:
- SwRS-OKFSCHEMA-CORE-001
- SwRS-OKFSCHEMA-CORE-006
---

## EARS Expression

### Normative behavior

When a maintainer validates an OKF bundle, the `okf-schema` CLI SHALL report
structural and schema violations without modifying the bundle's authored
content.

### Preserved stakeholder intent

## User Need

Maintainers need a deterministic way to establish whether an OKF bundle follows
its declared structure and schemas before they publish, exchange, or automate
work against it.

### Rationale and constraints

- Validation must preserve authored Markdown, frontmatter, comments, and unknown
  metadata.
- A structurally invalid bundle must be distinguishable from a valid bundle by
  both human-readable output and command exit status.

---
type: StRS
id: StRS-OKFSCHEMA-CORE-001
uuid: 7d6546eb-9bea-482c-9660-9f031d49970b
title: Validate OKF bundle structures
description: The generic CLI validates OKF bundle structure and schemas.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
scenarios:
- id: S1
  title: Validate a conforming bundle
- id: S2
  title: Report a non-conforming bundle without changing it
derives_from: []
user_need: Teams need deterministic validation of ordinary OKF bundles.
derived_by:
- SwRS-OKFSCHEMA-CORE-001
- SwRS-OKFSCHEMA-CORE-006
- SwRS-OKFSCHEMA-CORE-008
default_owner_email: gaetan@xeberon.net
tested_in_files:
- tests/test_cli_core.py
- tests/test_integration.py
accepted_in_files:
- tests/test_acceptance_core.py
---

## Validate OKF bundle structures

### Normative behavior

When a maintainer validates an OKF bundle, the `okf-schema` CLI SHALL report
structural and schema violations without modifying the bundle's authored
content.

### Main paths

#### Path S1: Validate a conforming bundle

1. the maintainer runs the `okf-schema validate` command on a bundle
2. the CLI reads the bundle's declared structure and schemas
3. the CLI reports no violation and exits with a success status

#### Path S2: Report a non-conforming bundle without changing it

1. the maintainer runs the `okf-schema validate` command on a bundle that breaks its own structure
2. the CLI reports each violation with its location and exits with a failure status
3. every file of the bundle is byte-for-byte unchanged

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

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-OKFSCHEMA-CORE-001](../../swrs/core/SwRS-OKFSCHEMA-CORE-001.md): Validate generic OKF bundles
  - [SwRS-OKFSCHEMA-CORE-006](../../swrs/core/SwRS-OKFSCHEMA-CORE-006.md): Validate OKF 0.2 provenance and lifecycle
  - [SwRS-OKFSCHEMA-CORE-008](../../swrs/core/SwRS-OKFSCHEMA-CORE-008.md): Report schema files that yield no schema
<!-- okf:links:end -->

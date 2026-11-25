---
type: StRS
id: StRS-OKFSCHEMA-OKFREQ-001
uuid: 23eea2f5-9ecd-4a21-bfdd-9c0825b45328
title: Maintain auditable software requirements
description: The okfreq capability SHALL enable teams to author, trace, and
  audit layered software requirements while preserving stable requirement
  identity and authored intent.
project: okf-schema
scope: okfreq
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Teams need auditable requirements traceability before delivery
  decisions.
scenarios:
- id: S1
  title: Set up a bundle and author linked requirements
- id: S2
  title: Trace markers and refresh generated coverage
- id: S3
  title: Audit the requirements base with validate and a report
derived_by:
- SwRS-OKFSCHEMA-OKFREQ-001
- SwRS-OKFSCHEMA-OKFREQ-002
- SwRS-OKFSCHEMA-OKFREQ-003
- SwRS-OKFSCHEMA-OKFREQ-004
- SwRS-OKFSCHEMA-OKFREQ-005
- SwRS-OKFSCHEMA-OKFREQ-006
- SwRS-OKFSCHEMA-OKFREQ-007
- SwRS-OKFSCHEMA-OKFREQ-008
- SwRS-OKFSCHEMA-OKFREQ-009
- SwRS-OKFSCHEMA-OKFREQ-010
- SwRS-OKFSCHEMA-OKFREQ-011
- SwRS-OKFSCHEMA-OKFREQ-012
- SwRS-OKFSCHEMA-OKFREQ-013
- SwRS-OKFSCHEMA-OKFREQ-014
- SwRS-OKFSCHEMA-OKFREQ-015
default_owner_email: gaetan@xeberon.net
tested_in_files:
- tests/test_examples.py
- tests/test_okfreq.py
accepted_in_files:
- tests/test_acceptance_okfreq.py
---

## Maintain auditable software requirements

### Normative behavior

The `okfreq` capability SHALL enable teams to author, trace, and audit layered
software requirements while preserving stable requirement identity and authored
intent.

### Preserved stakeholder intent

## User Need

Teams need a requirements base that connects stakeholder outcomes to testable
software behavior and supporting source and test evidence, so gaps and drift are
visible before delivery decisions are made.

### Rationale and constraints

- Stakeholder requirements and software requirements have distinct authoring
  formats and hierarchy roles.
- Coverage fields and reverse relationships are generated from explicit evidence;
  they are not assertions authored by hand.
- Lifecycle transitions remain explicit human decisions.
- Consumers must be able to distinguish local requirement navigation, project source/test
  evidence, and external tracker IDs while preserving existing requirement identity and values.

### Main paths

#### Path S1: Set up a bundle and author linked requirements

1. A maintainer initializes a requirements bundle with `okfreq init`.
2. The maintainer authors a stakeholder requirement and a derived software requirement with `okfreq new`.
3. Both documents are written with valid frontmatter, stable UUIDs, and declared derivation links.

#### Path S2: Trace markers and refresh generated coverage

1. Source and test files carry traceability markers referencing declared requirements and scenarios.
2. The maintainer runs `okfreq trace` and `okfreq update-coverage`.
3. `okfreq` discovers the markers and updates generated coverage and reverse-link fields without altering authored prose.

#### Path S3: Audit the requirements base with validate and a report

1. A maintained requirements bundle has refreshed coverage and navigation indexes.
2. The maintainer runs `okfreq validate` and `okfreq generate-report`.
3. Validation passes and JSON, JSON Schema, and Markdown reports are emitted with complete coverage metrics.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-OKFSCHEMA-OKFREQ-001](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-001.md): Provide requirements traceability operations
  - [SwRS-OKFSCHEMA-OKFREQ-002](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-002.md): Author and validate requirements
  - [SwRS-OKFSCHEMA-OKFREQ-003](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-003.md): Trace requirements to source and tests
  - [SwRS-OKFSCHEMA-OKFREQ-004](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-004.md): Report requirement health
  - [SwRS-OKFSCHEMA-OKFREQ-005](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-005.md): Validate requirement bundles
  - [SwRS-OKFSCHEMA-OKFREQ-006](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-006.md): Merge requirement configuration safely
  - [SwRS-OKFSCHEMA-OKFREQ-007](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-007.md): Manage requirement lifecycle explicitly
  - [SwRS-OKFSCHEMA-OKFREQ-008](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-008.md): Ship usable standalone requirements guidance
  - [SwRS-OKFSCHEMA-OKFREQ-009](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-009.md): Maintain generated requirement navigation
  - [SwRS-OKFSCHEMA-OKFREQ-010](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-010.md): Set up a project's requirements baseline from one skill
  - [SwRS-OKFSCHEMA-OKFREQ-011](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-011.md): Retire a draft requirement permanently
  - [SwRS-OKFSCHEMA-OKFREQ-012](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-012.md): Relate requirements by supersession and association
  - [SwRS-OKFSCHEMA-OKFREQ-013](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-013.md): Resolve requirement ownership and guard approvals
  - [SwRS-OKFSCHEMA-OKFREQ-014](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-014.md): Keep requirement bundles native OKF bundles
  - [SwRS-OKFSCHEMA-OKFREQ-015](../../swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-015.md): Measure StRS acceptance paths with declared scenarios
<!-- okf:links:end -->

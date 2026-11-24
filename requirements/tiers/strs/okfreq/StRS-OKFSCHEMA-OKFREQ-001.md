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

### Main paths

#### Path 1: Set up a bundle and author linked requirements

1. `okfreq init` creates a requirements bundle with its configuration and guideline.
2. `okfreq new strs` and `okfreq new swrs --derives-from` author a StRS and the SwRS that derive
   from it.
3. `okfreq lint` refreshes the generated navigation, and `okfreq validate` passes.
4. `okfreq graph` and `okfreq index` show the requirements and their derivation.

#### Path 2: Trace markers and refresh generated coverage

1. Source and test files carry `@implements_req` and `@tests_req` markers.
2. `okfreq trace --json` lists the markers by requirement.
3. `okfreq update-coverage --check` reports the stale generated fields without writing them.
4. `okfreq update-coverage` writes them, and the authored fields stay unchanged.

#### Path 3: Audit the requirements base with validate and a report

1. `okfreq validate --json` reports the bundle's findings.
2. `okfreq generate-report` writes the JSON report and the Markdown summary.
3. The report shows the coverage and the requirements that miss tests; the requirements are
   unchanged.

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

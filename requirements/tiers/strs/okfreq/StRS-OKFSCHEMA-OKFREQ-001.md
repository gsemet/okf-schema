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
lifecycle: draft
origin: native
tier: StRS
derives_from: []
user_need: Teams need auditable requirements traceability before delivery decisions.
derived_by:
- SwRS-OKFSCHEMA-OKFREQ-001
- SwRS-OKFSCHEMA-OKFREQ-002
- SwRS-OKFSCHEMA-OKFREQ-003
- SwRS-OKFSCHEMA-OKFREQ-004
- SwRS-OKFSCHEMA-OKFREQ-005
- SwRS-OKFSCHEMA-OKFREQ-006
- SwRS-OKFSCHEMA-OKFREQ-007
---

## EARS Expression

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

---
type: StRS
id: StRS-CORE-001
uuid: 00000000-0000-4000-8000-000000000001
title: Export a report
description: When export is requested, the reporting capability SHALL provide a
  portable report.
project: OKFREQXMP
scope: Core
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Users need a portable report for offline review.
derived_by:
- SwRS-CORE-001
- SwRS-CORE-002
---

## Export a report

### Normative behavior

When export is requested, the reporting capability SHALL provide a portable report.

### Preserved stakeholder intent

## User Need

Users need a portable report for offline review.

### Rationale and constraints

<!-- Record stakeholder constraints, exclusions, or decisions that shape the
     outcome. Remove this section when there are none. -->

- The report must remain usable offline and the requirement does not prescribe a specific portable format.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-CORE-001](../swrs/SwRS-CORE-001.md): Write CSV output
  - [SwRS-CORE-002](../swrs/SwRS-CORE-002.md): Format Rust CSV rows
<!-- okf:links:end -->

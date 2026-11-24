---
type: StRS
id: StRS-OKFSCHEMA-CORE-003
uuid: 9152112d-4e75-4fc3-97a5-c0e40172b740
title: Recognize file references without changing knowledge values
description: The OKF capability SHALL enable consumers to distinguish file
  references from ordinary strings and navigate their targets without changing
  authored value types.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Consumers need to recognize one file link or a list of file links
  without guessing from field names, while existing documents remain usable
  without migration.
scenarios:
- id: S1
  title: Navigate declared file links
- id: S2
  title: Check declared file links on request
derived_by:
- SwRS-OKFSCHEMA-CORE-007
default_owner_email: gaetan@xeberon.net
tested_in_files:
- tests/test_file_links.py
accepted_in_files:
- tests/test_acceptance_core.py
---

## Recognize file references without changing knowledge values

### Normative behavior

The OKF capability SHALL enable consumers to distinguish file references from ordinary strings and
navigate their targets without changing authored value types.

### Main paths

#### Path S1: Navigate declared file links

1. A consumer asks the shared API for the file links of a document whose schema
   declares them.
2. The API returns each target, with its root, for a single link and for a list
   of links, and the authored values stay strings and lists of strings.

#### Path S2: Check declared file links on request

1. A maintainer validates a bundle with link checking requested.
2. Each missing target is reported, and a check that could not run is reported as
   skipped instead of passing.

### Preserved stakeholder intent

## User Need

Parsers, editors, and agents need to recognize one file link or a list of file links and know where
each target is rooted. Property names and path-like text alone do not establish that meaning.
The same contract must apply to ordinary knowledge, engineering evidence, and requirements.

### Rationale and constraints

- File references remain strings; lists remain lists of strings.
- Checking targets is an explicit choice, not a new requirement for existing bundles.
- A skipped check must not be presented as evidence that a target exists.
- Existing bundles and their schemas require no automatic migration or rewrite.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-OKFSCHEMA-CORE-007](../../swrs/core/SwRS-OKFSCHEMA-CORE-007.md): Interpret and optionally check schema-declared file references
<!-- okf:links:end -->

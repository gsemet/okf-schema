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

#### Path 1: Navigate declared file links

1. A schema declares a frontmatter value as a file link with `x-okf-link` and names its root.
2. A consumer inspects a document's declared file links through the public API.
3. It gets each link's field, root and resolved target; the value stays the authored string.
4. The consumer opens the target.

#### Path 2: Check declared file links on request

1. A document declares a file link whose target is missing.
2. Default validation reports nothing about the target.
3. `okf-schema validate --check-links` reports `E10` naming the field and fails, without changing
   the bundle.
4. Once the target exists, the same check passes.

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

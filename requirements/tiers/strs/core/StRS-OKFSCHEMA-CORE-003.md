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

### Main paths

#### Path S1: Navigate declared file links

1. A bundle schema annotates string properties with `x-okf-link` while keeping authored values as plain strings or string lists.
2. A consumer calls the installed `inspect_file_links` API to resolve declared references.
3. The API resolves targets according to each declared resolution mode and reports target paths and any broken references without altering authored values.

#### Path S2: Check declared file links on request

1. A bundle contains a document with a schema-declared file reference whose target is missing.
2. A maintainer runs `okf-schema validate` without `--check-links` and then with `--check-links`.
3. Without `--check-links`, validation passes without checking targets; with `--check-links`, validation reports the missing target (`E10`) and exits non-zero.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-OKFSCHEMA-CORE-007](../../swrs/core/SwRS-OKFSCHEMA-CORE-007.md): Interpret and optionally check schema-declared file references
<!-- okf:links:end -->

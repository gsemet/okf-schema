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
lifecycle: draft
origin: native
tier: StRS
derives_from: []
user_need: Consumers need to recognize one file link or a list of file links
  without guessing from field names, while existing documents remain usable
  without migration.
derived_by:
- SwRS-OKFSCHEMA-CORE-007
---

## EARS Expression

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
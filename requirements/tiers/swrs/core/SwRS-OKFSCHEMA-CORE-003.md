---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-003
uuid: f2a61c68-7d76-4d47-aef2-8b191e2ad003
title: Normalize bundle formatting
description: When formatting or linting is requested, okf-schema SHALL normalize
  supported frontmatter and Markdown while preserving comments, semantic values,
  and authored content.
project: okf-schema
scope: core
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-002
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/_internal/yaml.py
- src/okf_schema/api.py
- src/okf_schema/cli.py
- src/okf_schema/formatter.py
tested_in_files:
- tests/test_api.py
- tests/test_formatter.py
---

## EARS Expression

### Normative behavior

When formatting or linting is requested, okf-schema SHALL normalize supported frontmatter and Markdown while preserving comments, semantic values, and authored content.

### Scenario: Normalize supported content

- GIVEN a bundle containing supported but non-canonical frontmatter or whitespace
- WHEN formatting or linting is applied
- THEN the resulting document uses canonical formatting while retaining its
  semantic values, comments, links, and Markdown body

### Scenario: Preview without writing

- GIVEN a document that would be changed by normalization
- WHEN the operation runs in check or diff mode
- THEN the command reports the pending change and leaves the document unchanged

### Verification notes

- Method: formatter, API, and CLI regression tests.
- Criteria: normalized output is idempotent, preservation-sensitive content is
  retained, and preview modes perform no writes.

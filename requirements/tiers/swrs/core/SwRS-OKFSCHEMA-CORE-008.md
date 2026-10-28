---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-008
uuid: 8efb5257-3963-4989-882f-e6447a4222d3
title: Report schema files that yield no schema
description: When a schema file in a schema database is empty, cannot be parsed
  or is not a mapping, okf-schema SHALL report it with the file name and leave
  the type without schema, as informational I1 for an empty file and as warning
  W17 otherwise.
project: okf-schema
scope: core
lifecycle: proposed
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/validator.py
tested_in_files:
- tests/test_api.py
- tests/test_cli_core.py
- tests/test_okfreq.py
- tests/test_validator.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/reference/validation-codes.md
- docs/source/reference/api.md
agent_skill_files:
- skills/okf-schema/SKILL.md
default_owner_email: gaetan@xeberon.net
---

## Report schema files that yield no schema

### Normative behavior

When a schema file in a schema database is empty, cannot be parsed or is not a mapping, okf-schema SHALL report it with the file name and leave the type without schema, as informational I1 for an empty file and as warning W17 otherwise.

### Scenario: Report an empty schema file informationally

- GIVEN a schema database holding an empty, whitespace-only or comment-only schema file in JSON,
  JSON5 or YAML format
- WHEN the schema database is loaded for validation
- THEN the report contains an informational `I1` entry naming the file, the type stays without
  schema, and `--strict` validation does not fail because of it

### Scenario: Warn about an unparsable or non-mapping schema file

- GIVEN a schema file with a syntax error, an unreadable file, or a top-level value that is not a
  mapping
- WHEN the schema database is loaded for validation
- THEN the report contains warning `W17` naming the file and the parser error, and the type stays
  without schema

### Scenario: Keep the legacy loader silent

- GIVEN a caller of `load_schema_database`
- WHEN a schema file is empty or unparsable
- THEN the call still returns only the mapping of usable schemas, without raising

### Verification notes

- Method: validator, API and CLI regression tests over the three schema formats.
- Criteria: each format yields `I1` or `W17` with the file name, `--strict` exits 0 for `I1` alone
  and 1 for `W17`, and the usable schemas of the same directory are still loaded.

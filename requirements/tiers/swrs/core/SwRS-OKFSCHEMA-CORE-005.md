---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-005
uuid: eb55b7d2-fdc8-41a9-b7b6-917e6ec59017
title: Inspect and query bundle knowledge
description: When a user inspects an OKF bundle, okf-schema SHALL provide
  deterministic list, show, search, graph, backlink, and statistics results
  without modifying the bundle.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-002
depends_on:
- SwRS-OKFSCHEMA-CORE-010
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/_internal/utils.py
- src/okf_schema/api.py
- src/okf_schema/cli.py
tested_in_files:
- tests/test_api.py
- tests/test_cli_remaining.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
scenarios:
- id: S1
  title: Inspect matching knowledge
- id: S2
  title: Reject an invalid inspection target
- id: S3
  title: Resolve a concept name without its extension
- id: S4
  title: Read a name from the bundle root
- id: S5
  title: Show a concept as stored
default_owner_email: gaetan@xeberon.net
---

## Inspect and query bundle knowledge

### Normative behavior

When a user inspects an OKF bundle, okf-schema SHALL provide deterministic list, show, search, graph, backlink, and statistics results without modifying the bundle.

### Scenario S1: Inspect matching knowledge

- GIVEN a valid bundle containing concepts and Markdown relationships
- WHEN the user lists, shows, searches, graphs, requests backlinks, or requests
  statistics
- THEN the command returns stable results derived from current bundle content

### Scenario S2: Reject an invalid inspection target

- GIVEN a missing bundle, a missing concept path, or a directory
- WHEN an inspection operation targets it
- THEN the operation reports an actionable not-found error without modifying any
  existing content

### Scenario S3: Resolve a concept name without its extension

- GIVEN a bundle with `api/health-check.md` (and possibly an `api/` directory
  beside an `api.md`)
- WHEN the user shows `api/health-check` or `api`
- THEN the exact path is used when it is a file, else the same name with `.md`
  added, and a directory is never shown

### Scenario S4: Read a name from the bundle root

- GIVEN a bundle with `api/health-check.md`
- WHEN the user shows `/api/health-check` or `api/health-check`, from any current
  working directory
- THEN both show the same concept, read from the bundle root; a leading `/` name
  with no such file in the bundle (for example `/etc/passwd`) is reported as not
  found and nothing outside the bundle is read

### Scenario S5: Show a concept as stored

- GIVEN a concept file in the bundle, whatever its frontmatter style, comments, line
  endings, encoding, or whether it has frontmatter or valid YAML at all
- WHEN the user shows it
- THEN the CLI writes the stored bytes to standard output, unchanged and with nothing
  added (no trust or staleness line), exits 0 and writes nothing to standard error,
  and the API result's `raw` holds the stored text of a UTF-8 file

### Verification notes

- Method: public API and CLI tests for list, show, search, graph, backlinks, and
  statistics operations.
- Criteria: ordering and computed relationships are deterministic, missing targets
  fail explicitly, and fixture content remains unchanged. A concept path resolves
  with or without `.md`, from the bundle root with or without a leading `/`, a
  directory is never shown, and the paths `show` accepts are bounded by
  SwRS-OKFSCHEMA-CORE-010. `show` output equals the stored file byte for byte,
  including a file without frontmatter, with invalid YAML, with CRLF line endings,
  or not valid UTF-8.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-CORE-002](../../strs/core/StRS-OKFSCHEMA-CORE-002.md): Maintain and inspect OKF bundles
- Depends on:
  - [SwRS-OKFSCHEMA-CORE-010](SwRS-OKFSCHEMA-CORE-010.md): Stay inside the bundle
<!-- okf:links:end -->

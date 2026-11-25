---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-004
uuid: 7ed42a5c-3866-4cad-9428-4a91173736d2
title: Maintain indexes and superseded links
description: When bundle maintenance is requested, okf-schema SHALL regenerate
  deterministic indexes and rewrite resolvable links to superseding concepts
  while reporting deferred rewrites.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-002
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/api.py
- src/okf_schema/cli.py
tested_in_files:
- tests/test_api.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
scenarios:
- id: S1
  title: Regenerate deterministic indexes
- id: S2
  title: Defer an unsafe superseded-link rewrite
- id: S3
  title: Write subdirectory summaries valid from the parent index
default_owner_email: gaetan@xeberon.net
---

## Maintain indexes and superseded links

### Normative behavior

When bundle maintenance is requested, okf-schema SHALL regenerate deterministic indexes and rewrite resolvable links to superseding concepts while reporting deferred rewrites.

### Scenario S1: Regenerate deterministic indexes

- GIVEN a bundle whose concepts or directory descriptions changed
- WHEN index or update maintenance runs
- THEN affected indexes are regenerated in deterministic order while preserved
  index frontmatter and authored descriptions remain intact

### Scenario S2: Defer an unsafe superseded-link rewrite

- GIVEN a link targets a superseded concept without a resolvable replacement
- WHEN bundle update runs
- THEN the link remains unchanged and the result reports why its rewrite was
  deferred

### Scenario S3: Write subdirectory summaries valid from the parent index

- GIVEN a subdirectory index with or without an introduction, and a parent index
  entry for that subdirectory that is missing, generic or damaged, with no schema
  summary applying
- WHEN index runs
- THEN the summary is the whole introduction before the first list, on one line,
  with its relative links rewritten to work from the parent index and cut at 120
  characters without splitting a link, or the generic sentence (also when the cut
  leaves nothing); other authored summaries are kept as written, whether the entry
  links `tables/`, `./tables/` or `./tables`; once every subdirectory index
  exists, a second run changes nothing

### Verification notes

- Method: API and CLI tests over indexed bundles and supersession fixtures.
- Criteria: repeated maintenance is idempotent, safe links are rewritten, and
  unresolved replacements are reported without data loss.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-CORE-002](../../strs/core/StRS-OKFSCHEMA-CORE-002.md): Maintain and inspect OKF bundles
<!-- okf:links:end -->

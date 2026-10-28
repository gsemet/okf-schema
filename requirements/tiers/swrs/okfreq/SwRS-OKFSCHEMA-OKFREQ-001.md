---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-001
uuid: 84d78e43-e518-466d-85a2-f98a3a5b9290
title: Provide requirements traceability operations
description: The okfreq subset provides requirement traceability operations.
project: okf-schema
scope: okfreq
lifecycle: proposed
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/cli.py
tested_in_files:
- tests/test_okfreq.py
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/reference/okfreq-cli.md
- docs/source/reference/okfreq-configuration.md
- docs/source/reference/okfreq-frontmatter.md
agent_skill_files:
- skills/okfreq/SKILL.md
- skills/okfreq/references/operations.md
- skills/okfreq-gardening/SKILL.md
example_files:
- examples/okfreq-examples/showcase.py
- examples/okfreq-examples/README.md
default_owner_email: gaetan@xeberon.net
---

## Provide requirements traceability operations

### Normative behavior

When a user invokes an `okfreq` command, the CLI SHALL provide deterministic
creation, validation, inspection, traceability, lifecycle, graph, and reporting
operations against the resolved requirements bundle.

### Scenario: Operate on a resolved bundle

- GIVEN a project containing one uniquely resolvable requirements bundle
- WHEN the user invokes an `okfreq` inspection command from the project or bundle
  path
- THEN the command operates on the bundle that owns `config.yml` and reports a
  stable result

### Scenario: Reject an invalid operation

- GIVEN an unknown requirement identity, invalid hierarchy target, or malformed
  bundle
- WHEN a mutating `okfreq` command is requested
- THEN the CLI exits unsuccessfully with an actionable error and avoids a partial
  write

### Scenario: Declare navigable references in new requirements schemas

- GIVEN an empty target for `okfreq init`
- WHEN the requirements scaffold is generated
- THEN string items in `derives_from`, `derived_by`, and `depends_on` declare
  `filename-stem`/`plain` links, and `implemented_in_files`/`tested_in_files` declare
  `project-relative`/`plain` links through the shared `x-okf-link` contract

Initialization preserves existing schemas. No existing requirement IDs, value types, or bundles
are migrated; `external_id` is not annotated as a local file link.

### Scenario: Install and refresh the shared guideline

- GIVEN a bundle that may already contain `guidelines/requirements.guidelines.md`
  and other guideline files
- WHEN the user runs `okfreq init` without `--force` on a bundle that has the
  guideline
- THEN the guideline is left untouched and the command reports that it was kept
- AND WHEN the user runs `okfreq init --force`, the guideline is replaced with the
  packaged text and the command reports it as replaced (or already up to date),
  while every other file of `guidelines/`, the configuration and the requirements
  are preserved
- AND a missing guideline is installed and reported as installed

### Verification notes

- Method: automated command-surface and failure-path tests.
- Criteria: supported commands resolve the same bundle consistently, and rejected
  operations preserve existing files.

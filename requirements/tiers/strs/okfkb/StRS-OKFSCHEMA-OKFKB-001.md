---
type: StRS
id: StRS-OKFSCHEMA-OKFKB-001
uuid: 37566aca-33fc-42e0-9def-995621c6f02b
title: Maintain trustworthy engineering knowledge
description: Teams can capture, organize, and mature engineering knowledge
  without losing evidence.
project: okf-schema
scope: okfkb
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Teams need to capture and organize engineering knowledge reliably.
scenarios:
- id: S1
  title: Capture an immutable finding
- id: S2
  title: Update a knowledge base's indexes and lint
- id: S3
  title: Propose a consolidation for human review
acceptance_exemption: true
acceptance_exemption_reason: >-
  Consolidation is an interactive agent skill requiring human review, not a
  deterministic console command that an automated acceptance test can execute.
derived_by:
- SwRS-OKFSCHEMA-OKFKB-001
- SwRS-OKFSCHEMA-OKFKB-002
- SwRS-OKFSCHEMA-OKFKB-003
- SwRS-OKFSCHEMA-OKFKB-004
- SwRS-OKFSCHEMA-OKFKB-005
- SwRS-OKFSCHEMA-OKFKB-006
default_owner_email: gaetan@xeberon.net
tested_in_files:
- tests/test_acceptance_okfkb.py
- tests/test_integration.py
accepted_in_files:
- tests/test_acceptance_okfkb.py
---

## Maintain trustworthy engineering knowledge

### Normative behavior

The `okfkb` capability SHALL enable engineering teams to capture, organize, and
mature knowledge while retaining the evidence and provenance on which that
knowledge depends.

### Main paths

#### Path S1: Capture an immutable finding

1. `okfkb init` scaffolds a knowledge base.
2. `okfkb new-finding` records a dated Finding with its confidence, context and tags, and the
   engineer writes the observation.
3. `okfkb update` and later Findings leave the Finding's authored body unchanged.
4. `okfkb get` returns the Finding, and the knowledge base validates.

#### Path S2: Update a knowledge base's indexes and lint

1. The knowledge base gains Findings and stable documents.
2. `okfkb update` writes the tier indexes and normalizes frontmatter, keeping authored text.
3. A second `okfkb update` changes nothing, and `okfkb validate` passes.

#### Path S3: Propose a consolidation for human review

1. The `okfkb-distill` skill, installed by `okfkb install-skills`, finds convergent Findings, for
   example with `okfkb query`.
2. It proposes a consolidation and writes it only after a human confirms.
3. The confirmed stable document names its Findings in `derived_from`, and `okfkb update` links the
   Findings back to it.
4. The Finding bodies stay unchanged, and `okfkb validate --check-links` passes.

### Preserved stakeholder intent

## User Need

Engineering teams need to turn observations into reusable understanding without
losing the original findings, confusing hypotheses with established knowledge,
or allowing automated maintenance to silently replace human judgment.

### Rationale and constraints

- Raw findings remain immutable evidence; maturation creates or updates the
  appropriate higher knowledge layer.
- Promotion or consolidation decisions that require judgment remain explicit and
  reviewable by a human.
- Consumers must be able to navigate from stable knowledge to its Finding files and inspect
  other file links without guessing their roots or changing evidence values.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derived by:
  - [SwRS-OKFSCHEMA-OKFKB-001](../../swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-001.md): Provide deterministic knowledge-base operations
  - [SwRS-OKFSCHEMA-OKFKB-002](../../swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-002.md): Scaffold and install knowledge bases
  - [SwRS-OKFSCHEMA-OKFKB-003](../../swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-003.md): Capture immutable knowledge findings
  - [SwRS-OKFSCHEMA-OKFKB-004](../../swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-004.md): Navigate knowledge-base evidence
  - [SwRS-OKFSCHEMA-OKFKB-005](../../swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-005.md): Consolidate knowledge findings
  - [SwRS-OKFSCHEMA-OKFKB-006](../../swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-006.md): Materialize reciprocal knowledge derivations
<!-- okf:links:end -->

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
  Path S3 (interactive consolidation for human review) is a human-in-the-loop
  agent skill workflow rather than a deterministic console command, so full
  automated acceptance across all three paths cannot be executed without
  human review; S1 and S2 carry automated installed-wheel acceptance tests.
derived_by:
- SwRS-OKFSCHEMA-OKFKB-001
- SwRS-OKFSCHEMA-OKFKB-002
- SwRS-OKFSCHEMA-OKFKB-003
- SwRS-OKFSCHEMA-OKFKB-004
- SwRS-OKFSCHEMA-OKFKB-005
- SwRS-OKFSCHEMA-OKFKB-006
default_owner_email: gaetan@xeberon.net
tested_in_files:
- tests/test_integration.py
accepted_in_files:
- tests/test_acceptance_okfkb.py
---

## Maintain trustworthy engineering knowledge

### Normative behavior

The `okfkb` capability SHALL enable engineering teams to capture, organize, and
mature knowledge while retaining the evidence and provenance on which that
knowledge depends.

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

### Main paths

#### Path S1: Capture an immutable finding

1. An engineer has an initialized `okfkb` knowledge base.
2. The engineer records a new empirical finding via `okfkb finding`.
3. A dated, immutable finding document is written with valid frontmatter and the knowledge base validates cleanly.

#### Path S2: Update a knowledge base's indexes and lint

1. A knowledge base contains captured findings and concepts whose indexes or reciprocal links need refreshing.
2. The maintainer runs `okfkb update` and `okfkb validate`.
3. Generated indexes and derivations are refreshed and validation passes without altering authored prose.

#### Path S3: Propose a consolidation for human review

1. Multiple empirical findings accumulate around a topic in the knowledge base.
2. An agent or maintainer uses the interactive `okfkb-distill` skill workflow to propose promotions or consolidations.
3. The human reviewer approves or rejects each proposed change before stable knowledge documents are updated.

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

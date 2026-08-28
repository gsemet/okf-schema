---
kind: wayfinder-ticket
title: Research federated knowledge-transfer semantics
status: open
labels:
  - 'wayfinder:research'
map: ../map.md
type: research
mode: HITL
assignee: null
blocked_by:
  - ./decide-gardening-supervision-boundary.md
  - ./decide-scoped-fact-ownership-contract.md
created_at: 2026-08-11T20:44:06Z
updated_at: 2026-08-11T20:44:06Z
---

## Question

What safe, evidence-preserving transfer semantics could connect related knowledge bases without
assuming that their DDD domains or vocabularies are identical? Investigate three directions:

- bottom-up distillation of genuinely generalisable facts from a lower-level KB;
- top-down transfer of generic, locally adoptable facts from a higher-level KB; and
- horizontal sharing between peer KBs with restricted or slightly different vocabularies.

For each direction, identify eligibility signals, source and receiving ownership, provenance,
scope translation, vocabulary/domain mappings, human review, conflict or rejection handling, and
how to avoid implying universal truth. Recommend small, disposable experiments that can distinguish
useful transfer from unsafe copying.

## Exploration boundary

This is a research ticket, not a federation architecture or implementation plan. Preserve the
possibility that some transfer directions are rejected, advisory-only, or require explicit human
re-authoring in the receiving KB.

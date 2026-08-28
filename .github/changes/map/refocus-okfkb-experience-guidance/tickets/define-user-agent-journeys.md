---
kind: wayfinder-ticket
title: Define the essential user and agent journeys
status: in_progress
labels:
  - 'wayfinder:grilling'
map: ../map.md
type: grilling
mode: HITL
assignee: Gaetan Semet
blocked_by: []
created_at: 2026-08-10T10:09:08Z
updated_at: 2026-08-11T20:44:06Z
---

## Question

What are the required happy paths, decisions, failure cases, and success signals for installing
into an existing repository, capturing a lesson after debugging, retrieving guidance before work,
curating experiences into approved guidance, correcting contradicted experience, and migrating a
current `okfkb` bundle? Include the distinction between human-driven and unattended gardening, the
visibility of scope and human ownership on hard facts, and the future journeys for transferring
reviewable knowledge between related knowledge bases.

## Direction confirmed during interview

These are the user-provided constraints to carry into later tickets. They are intentionally
journey-level expectations, not a final schema or implementation plan:

- Distillation is necessarily supervised by a human through `skills/okfkb-gardening/SKILL.md`.
- If no human drives the gardening execution, including a scheduled run, gardening may only
  consolidate what is safe. It must not distill Findings into hard facts or maintained guidance.
- Every hard fact must declare a subdivision of the KB as its scope and identify a human owner.
- The future model should support carefully governed movement between related KBs: generalisable
  facts may move from a lower-level KB upward, suitable generic facts may move from a higher-level
  KB downward, and peer KBs may share horizontally.
- Transfer cannot assume identical domains or vocabularies. Domain compatibility, restricted
  vocabulary mapping, provenance, receiving ownership, and human review must be visible parts of
  any later journey.

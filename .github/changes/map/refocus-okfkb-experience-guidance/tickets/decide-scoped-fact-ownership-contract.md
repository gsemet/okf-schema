---
kind: wayfinder-ticket
title: Define scoped hard facts and human ownership
status: open
labels:
  - 'wayfinder:grilling'
map: ../map.md
type: grilling
mode: HITL
assignee: null
blocked_by:
  - ./define-user-agent-journeys.md
created_at: 2026-08-11T20:44:06Z
updated_at: 2026-08-11T20:44:06Z
---

## Question

What is a hard fact in relation to an immutable Finding, approved guidance, and any future stable
semantic layer? Decide how every hard fact names a subdivision of its KB as scope, identifies a
human owner, preserves supporting evidence and provenance, and expresses lifecycle state. Explore
scope nesting, cross-scope applicability, owner replacement or absence, review responsibility, and
what deterministic checks can verify without claiming that a fact is universally true.

## Exploration boundary

This ticket is about meaning, accountability, and review journeys. It must not implement a schema,
permission service, or ownership UI. The final contract should leave room for facts that are later
selected for cross-KB transfer without making transfer automatic.

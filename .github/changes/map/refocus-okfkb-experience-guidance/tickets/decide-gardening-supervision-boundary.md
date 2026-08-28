---
kind: wayfinder-ticket
title: Define the gardening supervision and distillation boundary
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

What evidence distinguishes a human-driven gardening session from an unattended or scheduled
session, and which operations are permitted in each mode? Decide whether unattended gardening may
repair links, reconcile contradictions, append lifecycle metadata, and propose experiments while
forbidding distillation into hard facts or maintained guidance; then define how a human-supervised
run may review, accept, defer, or reject distillation proposals without granting autonomous agent
approval.

## Exploration boundary

This ticket defines the governance and user-visible journey only. It must not choose CLI commands,
implement authentication or scheduling, or silently introduce a schema for hard facts. Those
questions belong to later contracts after the supervision distinction is understood.

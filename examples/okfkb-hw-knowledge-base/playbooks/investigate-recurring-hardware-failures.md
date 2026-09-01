---
type: Playbook
title: Investigate recurring hardware failures
description: Reproduce and isolate a hardware failure signature without losing
  the original test boundary.
tags: [hardware, failure, investigation, stress-testing]
kb_status: active
derived_from: [concepts/hardware-failures-have-a-stress-signature]
# knowledge graph fields generated automatically — do not edit manually
derives_to: []
estimated_duration: 2 h
tools_required: [production logs, stress-test harness]
links: []
backlinks: []
generated:
  at: '2026-07-05T10:00:00Z'
  by: human:maintainer
---

# Investigate recurring hardware failures

1. Preserve the failing production logs and the exact stress-test parameters.
2. Reproduce the signature without changing more than one condition at a time.
3. Compare timestamps, affected components, and environmental boundaries.
4. Record each confirmed observation as a new Finding.

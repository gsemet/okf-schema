---
type: Concept
title: Hardware failures have a stress signature
description: Recurring production-log failures observed under stress testing
  form a reusable diagnostic signature.
tags: [hardware, failure, stress-testing, diagnostics]
kb_status: active
derived_from: [findings/2026.07.04-21.35-hw-failure-investigation]
# knowledge graph fields generated automatically — do not edit manually
derives_to: [playbooks/investigate-recurring-hardware-failures]
links: []
backlinks: []
generated:
  at: '2026-07-05T09:00:00Z'
  by: human:maintainer
---

# Hardware stress signature

Hardware failures that recur only during stress testing should be treated as a
bounded diagnostic signature. Preserve the production-log conditions before
changing hardware, firmware, or test parameters.

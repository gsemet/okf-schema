---
type: Concept
title: Fault Detection
description: BMS algorithms and hardware that detect abnormal conditions and
  trigger protective actions.
tags: [safety, bms, diagnostics]
timestamp: 2026-06-30T10:35:00Z
---

# Overview

Fault detection is the BMS capability to identify abnormal operating
conditions — such as over-voltage, under-voltage, over-temperature,
or over-current — and respond with appropriate protective actions.

# Detection Hierarchy

1. **Warning** — condition approaching limit; log and notify.
2. **Derating** — reduce power to bring condition back to safe range.
3. **Shutdown** — disconnect contactors to isolate the pack.

# Fault Categories

| Category | Monitored Parameter | Typical Threshold |
|----------|---------------------|-------------------|
| Over-voltage | Cell voltage | > 4.25 V |
| Under-voltage | Cell voltage | < 2.50 V |
| Over-temperature | Cell temperature | > 45 degC |
| Over-current | Pack current | > 3C rate |

# Related Concepts

- See [ASIL Rating](asil-rating.md) for safety integrity requirements.
- See [Safe Operating Area](safe-operating-area.md) for the boundaries.
- See [Temperature Sensors](../thermal/temperature-sensors.md) for inputs.

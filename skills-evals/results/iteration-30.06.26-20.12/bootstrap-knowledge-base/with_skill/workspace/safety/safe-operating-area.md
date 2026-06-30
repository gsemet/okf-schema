---
type: Concept
title: Safe Operating Area
description: Defined boundaries of voltage, current, and temperature within
  which cells operate safely.
tags: [safety, limits, operational]
timestamp: 2026-06-30T10:40:00Z
---

# Overview

The Safe Operating Area (SOA) defines the envelope of voltage, current,
and temperature conditions within which a lithium-ion cell can operate
without risk of damage, degradation acceleration, or safety incidents.

# SOA Boundaries

| Parameter | Lower Limit | Upper Limit | Violation Risk |
|-----------|-------------|-------------|----------------|
| Cell voltage | 2.5 V | 4.25 V | Degradation, plating, runaway |
| Cell temperature | -20 degC | 45 degC | Reduced life, thermal runaway |
| Charge current | 0 A | 1C (typical) | Lithium plating, overheating |
| Discharge current | 0 A | 3C (typical) | Overheating, voltage collapse |

# Related Concepts

- See [Cell Aging](../cells/cell-aging.md) for degradation outside SOA.
- See [Thermal Runaway](../thermal/thermal-runaway.md) for the extreme failure mode.
- See [Fault Detection](fault-detection.md) for enforcement mechanisms.

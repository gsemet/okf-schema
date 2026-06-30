---
type: Sensor
title: Temperature Sensors
description: Distributed temperature measurement devices monitoring cell and
  pack temperatures.
tags: [thermal, sensor, monitoring]
timestamp: 2026-06-30T10:25:00Z
---

# Overview

Temperature sensors are distributed throughout the battery pack to
provide real-time thermal data to the Battery Management System (BMS).
Accurate temperature monitoring is essential for safety and performance.

# Sensor Types

| Type | Accuracy | Response Time | Cost |
|------|----------|---------------|------|
| NTC thermistor | +/- 1 degC | Fast | Low |
| PT100/PT1000 | +/- 0.3 degC | Medium | Medium |
| Fiber-optic | +/- 0.5 degC | Fast | High |

# Placement

Sensors are typically placed on cell surfaces, cold plates, and at
inlet/outlet of coolant channels. The BMS uses the maximum reading
to trigger derating or shutdown.

# Related Concepts

- See [Thermal Runaway](thermal-runaway.md) for the event they detect.
- See [Cooling System](cooling-system.md) for the system they control.
- See [Fault Detection](../safety/fault-detection.md) for alarm thresholds.

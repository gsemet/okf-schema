---
type: Concept
title: Thermal Runaway
description: Uncontrolled self-heating reaction leading to cell failure and
  potential fire.
tags: [thermal, safety, failure-mode]
timestamp: 2026-06-30T10:15:00Z
---

# Overview

Thermal runaway is a catastrophic failure mode in lithium-ion cells
where an exothermic reaction generates heat faster than it can be
dissipated, leading to a self-sustaining temperature rise.

# Triggers

- Internal short circuit (dendrite growth, separator failure)
- External short circuit
- Overcharging beyond safe voltage limits
- Mechanical abuse (crush, penetration)
- Elevated ambient temperature

# Propagation

Once one cell enters thermal runaway, heat can propagate to neighboring
cells through conductive and radiative heat transfer. The [Cooling
System](cooling-system.md) is the primary defense against propagation.

# Related Concepts

- See [Cooling System](cooling-system.md) for thermal management strategies.
- See [Temperature Sensors](temperature-sensors.md) for early detection.
- See [Fault Detection](../safety/fault-detection.md) for BMS response protocols.

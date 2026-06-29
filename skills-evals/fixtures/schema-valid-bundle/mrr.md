---
type: metric
title: Monthly Recurring Revenue
description: Sum of all active subscription values normalized to a 30-day month.
timestamp: "2026-01-15T09:00:00Z"
formula: SUM(subscription_value * days_in_month / billing_cycle_days)
unit: currency
refresh_frequency: daily
---

# Monthly Recurring Revenue (MRR)

MRR is the primary revenue metric for the SaaS analytics dashboard.

## Definition

Sum of all active subscription values, normalized to a 30-day month.

## Related Concepts

- [users](users.md) — user accounts that generate subscriptions

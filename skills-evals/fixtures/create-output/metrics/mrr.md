---
type: Metric
title: Monthly Recurring Revenue
description: Sum of normalized monthly revenue from active SaaS subscriptions.
timestamp: 2026-06-23T00:00:00Z
tags:
  - saas
  - revenue
  - mrr
---

# Monthly Recurring Revenue

Monthly Recurring Revenue (MRR) is the sum of `monthly_amount` for active rows in
[Subscriptions](../tables/subscriptions.md). Analysts often segment MRR by attributes
from [Users](../tables/users.md), such as plan tier or signup cohort.

## Definition

MRR includes only recurring subscription revenue and excludes one-time fees.

## Formula

`MRR = Σ(monthly_amount for active subscriptions)`

# Examples

```sql
SELECT SUM(monthly_amount) AS mrr
FROM `saas_analytics.subscriptions`
WHERE status = 'active';
```

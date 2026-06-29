---
type: Metric
title: Gross Revenue
description: Total revenue before refunds and discounts.
tags: [revenue, finance, kpi]
timestamp: 2026-05-28T14:30:00Z
---

# Definition

Sum of `total_usd` from [orders](/tables/orders.md) for a given period.
Does not subtract refunds — see Net Revenue for that.

# SQL

```sql
SELECT DATE_TRUNC(placed_at, MONTH) as month,
       SUM(total_usd) as gross_revenue
FROM `acme.sales.orders`
GROUP BY 1
```

# Related

- Source table: [orders](/tables/orders.md)

---
type: BigQuery Table
title: Subscriptions
description: Table of subscription contracts, billing intervals, and lifecycle status for each SaaS customer.
timestamp: 2026-06-23T00:00:00Z
resource: bigquery://saas_analytics.subscriptions
tags:
  - saas
  - subscriptions
  - billing
---

# Subscriptions

The `subscriptions` table tracks each customer's recurring contract, including the
billing amount and whether the subscription is active. Each record links back to
[Users](./users.md) through `user_id`, and active rows feed the
[MRR](../metrics/mrr.md) metric.

# Schema

| Column | Type | Description |
| ------ | ---- | ----------- |
| `subscription_id` | STRING | Unique identifier for the subscription contract. |
| `user_id` | STRING | Foreign key to [Users](./users.md). |
| `monthly_amount` | NUMERIC | Normalized monthly recurring charge for the subscription. |
| `status` | STRING | Current lifecycle state such as active, paused, or canceled. |
| `start_date` | DATE | Date the subscription started. |

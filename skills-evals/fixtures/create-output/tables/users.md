---
type: BigQuery Table
title: Users
description: Dimension table containing one row per SaaS user account used for product and revenue analysis.
timestamp: 2026-06-23T00:00:00Z
resource: bigquery://saas_analytics.users
tags:
  - saas
  - users
  - dimensions
---

# Users

The `users` table stores the canonical user profile for the SaaS analytics domain.
It is commonly joined to [Subscriptions](./subscriptions.md) on `user_id` to understand
which accounts contribute to [MRR](../metrics/mrr.md).

# Schema

| Column | Type | Description |
| ------ | ---- | ----------- |
| `user_id` | STRING | Stable unique identifier for the user account. |
| `email` | STRING | Primary email address used for communication and login. |
| `signup_date` | DATE | Date when the user created an account. |
| `plan_tier` | STRING | Latest known plan tier associated with the user. |

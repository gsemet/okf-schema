---
type: BigQuery Table
title: Customers
description: One row per registered customer with profile and lifetime data.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=customers
tags: [sales, customers]
timestamp: 2026-05-28T14:30:00Z
---

# Schema

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | STRING | Primary key |
| `email` | STRING | Customer email (hashed in prod) |
| `created_at` | TIMESTAMP | Registration date |

# Joins

- Referenced by [orders](./orders.md) on `customer_id`

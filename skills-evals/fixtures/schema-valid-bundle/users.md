---
type: table
title: users
description: Core user accounts table containing registration and profile data.
timestamp: "2026-01-15T09:00:00Z"
owner: data-platform
tier: gold
pii: true
---

# users

The `users` table is the central identity store for the SaaS platform.

## Columns

| Column      | Type      | Description                |
|-------------|-----------|----------------------------|
| user_id     | UUID      | Primary key                |
| email       | VARCHAR   | Unique user email          |
| created_at  | TIMESTAMP | Account creation time      |

## Related Concepts

- [mrr](mrr.md) — revenue tied to active users

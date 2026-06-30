---
type: api-endpoint
title: Get User
description: Retrieve a user by their unique identifier.
timestamp: 2026-06-30T13:52:00Z
method: GET
path: /api/v1/users/{id}
---

# Get User

Retrieve detailed information about a user.

## Request

```http
GET /api/v1/users/{id}
```

## Response

```json
{
  "id": "123",
  "name": "Alice"
}
```

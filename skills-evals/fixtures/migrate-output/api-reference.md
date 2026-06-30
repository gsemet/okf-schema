---
type: reference
title: API Reference
description: REST API endpoints for the EV Battery Management System.
tags: [api, reference, endpoints]
timestamp: 2026-06-30T14:00:00Z
---

# API Reference

## Endpoints

### GET /battery/status

Returns the current battery status including SoC, voltage, and temperature.

### POST /battery/charge

Initiates a charging session with the specified parameters.

## Authentication

All endpoints require a valid API key passed in the `X-API-Key` header.

## Related Documents

- See [System Architecture](architecture.md) for component overview.
- See [Troubleshooting](troubleshooting.md) for common errors.

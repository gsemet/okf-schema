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

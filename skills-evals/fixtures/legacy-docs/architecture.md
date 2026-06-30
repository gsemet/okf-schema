# System Architecture

## Overview

This document describes the high-level architecture of the EV Battery Management System.

## Components

- **Battery Controller**: Monitors cell voltages and temperatures.
- **Thermal Management**: Regulates battery pack temperature.
- **State of Charge (SoC) Estimator**: Calculates remaining capacity.

## Data Flow

Sensor data flows from the Battery Controller to the SoC Estimator, then to the Vehicle Gateway.

## Related Documents

- See [API Reference](api-reference.md) for interface definitions.
- See [Deployment Guide](deployment-guide.md) for installation steps.

---
type: Playbook
title: Deployment Guide
description: Step-by-step guide to deploy the EV Battery Management System.
tags: [bms, ev, deployment, operations]
timestamp: 2026-06-30T13:52:00Z
---

# Deployment Guide

## Prerequisites

- Docker 20.10+
- Kubernetes 1.25+
- Helm 3.12+

## Installation

1. Clone the repository.
2. Run `helm install bms ./chart`.
3. Verify pods are running with `kubectl get pods`.

## Configuration

Edit `values.yaml` to configure resource limits and replica counts.

## Related Documents

- See [System Architecture](../architecture.md) for component details.
- See [Troubleshooting](./troubleshooting.md) for debugging tips.

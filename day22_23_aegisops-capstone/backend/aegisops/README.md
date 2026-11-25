# AegisOps Backend Package

## Overview

This Python package contains the FastAPI application logic and supporting
services for the AegisOps incident assistant.

## Business purpose

The package joins validated, read-only operational metrics with role-scoped
document retrieval and LLM synthesis, while exposing service health and
telemetry to the UI and monitoring systems.

## Key components

- `api.py` defines API endpoints, bearer-token validation, role handling,
  configuration, and Prometheus instrumentation.
- `assistant.py` coordinates safe metric queries, Markdown/vector retrieval,
  source attribution, and answer generation.
- `ingestion.py` provides DuckDB SLA data loading, PII redaction, embedding,
  and post-mortem ingestion helpers.
- `metrics.py` records request latency, LLM usage/cost estimates,
  circuit-breaker state, and PII-redaction counts.

The package is launched from the capstone project root with
`PYTHONPATH=backend uvicorn aegisops.api:app`. See the parent
[`backend/README.md`](../README.md) for configuration and setup.

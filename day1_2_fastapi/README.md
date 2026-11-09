# Day 1-2: FastAPI Ingestion API

## Overview
This module demonstrates an enterprise-grade ingestion service built with FastAPI. It focuses on structured logging, request correlation, strict API validation, and in-memory persistence for a demo environment.

## Business purpose
The service accepts incident payloads from downstream systems, normalizes messy input values, and stores validated records for later inspection. It is designed to represent the first step of an operational data pipeline where production-grade reliability is required even in a lightweight demo application.

## Key components

### FastAPI application
The service is defined in `main.py` and exposes:
- `GET /healthz` for liveness and simple status checks
- `POST /api/v1/ingest` for normalized incident ingestion

### Correlation ID middleware
A custom ASGI middleware adds a request correlation ID from the `X-Correlation-ID` header or generates one automatically. It also injects response headers:
- `X-Correlation-ID`
- `X-Process-Time-Ms`

This is useful for tracing a single request across logs, downstream processing, and operational dashboards.

### Pydantic validation and normalization
The API uses a `LegacyIncidentPayload` model with strict validation and data cleanup logic:
- tenant IDs are normalized to lowercase and whitespace-safe names
- severity values are mapped from dirty legacy formats like `P1`, `SEV2`, `WARN`, or `1` to canonical values such as `CRITICAL`, `HIGH`, and `MEDIUM`
- required fields are enforced before any record is accepted

### In-memory storage
The application keeps a list of accepted incidents in memory to support demonstration and debugging. This is intentionally simple and not production-persistent storage.

## Request flow
1. Client sends an incident payload to `/api/v1/ingest`.
2. FastAPI validates input using the `LegacyIncidentPayload` schema.
3. Severity and tenant values are normalized.
4. The application adds metadata such as correlation ID and UTC ingest timestamp.
5. The record is appended to the in-memory list and returned as a normalized response.

## Example payload
```json
{
  "tenant_id": "Acme Corp",
  "raw_severity": "P1",
  "service_name": "billing-api",
  "error_message": "Database failover triggered",
  "tags": ["db", "prod"],
  "reported_at": "2026-11-06T12:00:00Z"
}
```

## Example response
```json
{
  "status": "ingested",
  "normalized_record": {
    "tenant_id": "acme_corp",
    "raw_severity": "CRITICAL",
    "service_name": "billing-api",
    "error_message": "Database failover triggered",
    "tags": ["db", "prod"],
    "reported_at": "2026-11-06T12:00:00Z",
    "correlation_id": "fde-xxxx",
    "ingested_at_utc": "2026-11-06T12:00:00.123456"
  }
}
```

## Run it
From the repository root:

```bash
cd day1_2_fastapi
pip install -r requirements.txt
uvicorn main:app --reload
```

## Best use cases
- API contract prototyping
- Data ingestion normalization from legacy sources
- Logging and traceability exercises
- Lightweight service design experiments

## Notes
This folder is intentionally simple and demonstrates the first layer of an event-driven enterprise platform: robust input handling and observability at the API edge.

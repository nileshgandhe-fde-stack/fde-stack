# Day 3: Flaky Legacy Integration and Resilience Patterns

## Overview
This module models a legacy enterprise dependency that is unreliable under real-world conditions. It demonstrates how to protect a client application from temporary outages, throttling, and noisy upstream failures using retries, jitter, and circuit breaking.

## Business purpose
In enterprise systems, internal or third-party dependencies often fail intermittently. This example simulates a legacy ERP system that sometimes returns:
- `503 Service Unavailable`
- `429 Too Many Requests`
- transient network-style errors

The goal is to show how to make dependent workflows tolerant without hiding persistent failures.

## Key components

### Circuit breaker
The `CircuitBreaker` class tracks consecutive failures and transitions between states:
- `CLOSED`: requests flow normally
- `OPEN`: requests are blocked temporarily after threshold breach
- `HALF_OPEN`: a probe state allows recovery checks

The breaker is tuned to trip after repeated failures and then cool down before accepting new requests again.

### Mock flaky upstream service
The `mock_legacy_erp_handler` function simulates a legacy ERP endpoint using `httpx.MockTransport`. It randomly returns:
- a successful payload
- a `503` error
- a `429` rate-limit response

This gives realistic failure patterns for testing resilience logic without needing a real external service.

### Retry with exponential backoff and jitter
The `fetch_page_with_retry` function is wrapped with `tenacity`:
- retries up to a fixed number of attempts
- uses randomized exponential backoff
- re-raises exceptions after the configured retry budget is exhausted

This prevents tight retry loops and reduces thundering-herd behavior during upstream issues.

### Httpx client configuration
The asynchronous client uses:
- a mock transport for deterministic local behavior
- connection limits for resource control
- a timeout for request safety

## Failure handling strategy
When a page fetch receives a status code such as `429`, `500`, `502`, `503`, or `504`, the code:
1. records a failure in the circuit breaker
2. logs the issue with page number and HTTP status
3. raises the error so `tenacity` can retry

If the breaker remains open, subsequent requests pause briefly before re-attempting.

## Processing flow
1. The application loops through page numbers 1-15.
2. A request is made to the legacy ERP endpoint.
3. If the upstream returns a transient failure, the breaker records it and the request is retried with jitter.
4. When the service stabilizes, the breaker resets and subsequent requests succeed.

## Example behavior
The script prints output similar to:
- `Page 01 synced successfully | Breaker State: CLOSED | ...`
- `⚠️ Page 04 failed with HTTP 503 -> Retrying with backoff+jitter...`
- `🟡 [CIRCUIT BREAKER] Moving to HALF_OPEN probe state...`

## Run it
```bash
cd day3_flaky_legacy
python flaky_server_and_client.py
```

## Best use cases
- Resilience training for third-party APIs
- Circuit breaker design exercises
- Retry policy tuning
- Delayed or intermittent integration testing

## Notes
This folder is a practical example of defensive engineering: operations should fail gracefully, back off intelligently, and avoid cascading failures when upstream systems are unstable.

# Runbook: database connection-pool saturation

## Signals

Connection-pool saturation often coincides with elevated database wait time,
application latency, and an increase in request timeouts or 5xx responses.
Compare connection usage and errors with the affected service's SLA metrics.

## Mitigation

1. Check database health and connection counts before increasing pool limits.
2. Identify recent query or deployment changes and roll back a harmful change.
3. Reduce excess worker concurrency if it is exhausting the shared pool.
4. Verify error rate, latency, and connection usage have recovered.

Avoid increasing connection limits without checking database capacity; that can
move the saturation point without resolving the underlying cause.
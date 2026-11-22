# Runbook: worker capacity and queue backlog

## Signals

Queue depth that rises while worker capacity falls can indicate a deployment,
configuration drift, or dependency slowdown. Compare backlog age, worker
restarts, and service error metrics.

## Mitigation

1. Check worker health and recent configuration or deployment changes.
2. Restore the last known-good worker configuration if capacity dropped after a
   change.
3. Scale workers only after confirming the downstream dependency can accept the
   additional concurrency.
4. Drain the backlog gradually and verify queue age and SLA metrics recover.
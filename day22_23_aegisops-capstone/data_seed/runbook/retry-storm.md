# Runbook: retry storms and elevated 5xx responses

## Signals

Look for a rising 5xx rate, increasing request latency, and retry volume growing
faster than incoming traffic. A dependency slowdown can cause clients and workers
to retry together, amplifying load on the original dependency.

## Mitigation

1. Check dependency latency and connection-pool saturation before restarting
   healthy application instances.
2. Reduce retry concurrency and confirm exponential backoff and jitter are
   enabled.
3. If a recent deployment changed retry behavior, roll it back and compare the
   5xx rate and queue depth against the pre-deployment baseline.
4. Confirm recovery using the service-level objective and continue monitoring
   until retry volume returns to normal.

## Follow-up

Add a regression test for retry amplification, cap retries, and update alerts to
track both dependency errors and retry volume.
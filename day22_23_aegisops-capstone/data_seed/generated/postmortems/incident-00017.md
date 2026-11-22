# Post-mortem: order-worker incident INC-00017

## Summary

On 2026-07-14T19:22:20Z, the order-worker service in us-east-1 experienced an interruption lasting
approximately 239 minutes. Read replicas returned stale data while the primary recovered.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `order-worker`
- Responsible team: Identity
- Severity: SEV-2
- Customer impact window: 239 minutes
- Tenant impact estimate: 26 tenants

## Timeline

- 2026-07-14T19:22:20Z — Alert fired; on-call engineer acknowledged the incident.
- 119 minutes later — Mitigation started and error rate began to fall.
- 239 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact027@example.com | +1-202-555-0127

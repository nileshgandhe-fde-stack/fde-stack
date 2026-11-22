# Post-mortem: order-worker incident INC-00027

## Summary

On 2026-09-14T01:21:50Z, the order-worker service in us-west-2 experienced an interruption lasting
approximately 58 minutes. Read replicas returned stale data while the primary recovered.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `order-worker`
- Responsible team: Platform
- Severity: SEV-2
- Customer impact window: 58 minutes
- Tenant impact estimate: 17 tenants

## Timeline

- 2026-09-14T01:21:50Z — Alert fired; on-call engineer acknowledged the incident.
- 29 minutes later — Mitigation started and error rate began to fall.
- 58 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact037@example.com | +1-202-555-0137

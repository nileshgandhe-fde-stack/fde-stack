# Post-mortem: order-worker incident INC-00018

## Summary

On 2026-09-09T11:24:16Z, the order-worker service in us-west-2 experienced an interruption lasting
approximately 12 minutes. Read replicas returned stale data while the primary recovered.
Initial impact estimates were revised during review.

## Impact

- Affected service: `order-worker`
- Responsible team: Data Operations
- Severity: SEV-1
- Customer impact window: 12 minutes
- Tenant impact estimate: 31 tenants

## Timeline

- 2026-09-09T11:24:16Z — Alert fired; on-call engineer acknowledged the incident.
- 6 minutes later — Mitigation started and error rate began to fall.
- 12 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact028@example.com | +1-202-555-0128

# Post-mortem: order-worker incident INC-00025

## Summary

On 2026-10-31T05:07:13Z, the order-worker service in us-east-1 experienced an interruption lasting
approximately 120 minutes. Read replicas returned stale data while the primary recovered.
Initial impact estimates were revised during review.

## Impact

- Affected service: `order-worker`
- Responsible team: Payments
- Severity: SEV-1
- Customer impact window: 120 minutes
- Tenant impact estimate: 45 tenants

## Timeline

- 2026-10-31T05:07:13Z — Alert fired; on-call engineer acknowledged the incident.
- 60 minutes later — Mitigation started and error rate began to fall.
- 120 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact035@example.com | +1-202-555-0135

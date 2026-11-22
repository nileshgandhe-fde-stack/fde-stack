# Post-mortem: order-worker incident INC-00048

## Summary

On 2026-08-28T04:12:37Z, the order-worker service in us-west-2 experienced an interruption lasting
approximately 131 minutes. Read replicas returned stale data while the primary recovered.

## Impact

- Affected service: `order-worker`
- Responsible team: Identity
- Severity: SEV-3
- Customer impact window: 131 minutes
- Tenant impact estimate: 45 tenants

## Timeline

- 2026-08-28T04:12:37Z — Alert fired; on-call engineer acknowledged the incident.
- 65 minutes later — Mitigation started and error rate began to fall.
- 131 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact058@example.com | +1-202-555-0158

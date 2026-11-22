# Post-mortem: order-worker incident INC-00002

## Summary

On 2026-03-08T13:10:55Z, the order-worker service in ap-southeast-2 experienced an interruption lasting
approximately 71 minutes. Background reconciliation fell behind its normal processing window.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `order-worker`
- Responsible team: Identity
- Severity: SEV-3
- Customer impact window: 71 minutes
- Tenant impact estimate: 33 tenants

## Timeline

- 2026-03-08T13:10:55Z — Alert fired; on-call engineer acknowledged the incident.
- 35 minutes later — Mitigation started and error rate began to fall.
- 71 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact012@example.com | +1-202-555-0112

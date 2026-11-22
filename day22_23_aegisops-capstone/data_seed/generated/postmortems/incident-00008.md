# Post-mortem: order-worker incident INC-00008

## Summary

On 2026-04-30T02:28:48Z, the order-worker service in us-west-2 experienced an interruption lasting
approximately 87 minutes. Checkout requests timed out for a subset of tenants.

## Impact

- Affected service: `order-worker`
- Responsible team: Platform
- Severity: SEV-1
- Customer impact window: 87 minutes
- Tenant impact estimate: 42 tenants

## Timeline

- 2026-04-30T02:28:48Z — Alert fired; on-call engineer acknowledged the incident.
- 43 minutes later — Mitigation started and error rate began to fall.
- 87 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact018@example.com | +1-202-555-0118

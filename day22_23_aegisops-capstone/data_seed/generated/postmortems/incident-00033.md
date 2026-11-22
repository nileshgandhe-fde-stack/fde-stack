# Post-mortem: order-worker incident INC-00033

## Summary

On 2026-06-03T19:50:30Z, the order-worker service in eu-west-1 experienced an interruption lasting
approximately 193 minutes. Checkout requests timed out for a subset of tenants.
Initial impact estimates were revised during review.

## Impact

- Affected service: `order-worker`
- Responsible team: Customer Experience
- Severity: SEV-2
- Customer impact window: 193 minutes
- Tenant impact estimate: 19 tenants

## Timeline

- 2026-06-03T19:50:30Z — Alert fired; on-call engineer acknowledged the incident.
- 96 minutes later — Mitigation started and error rate began to fall.
- 193 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact043@example.com | +1-202-555-0143

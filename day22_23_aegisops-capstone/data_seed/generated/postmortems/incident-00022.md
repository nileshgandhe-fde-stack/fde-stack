# Post-mortem: order-worker incident INC-00022

## Summary

On 2025-12-07T19:42:37Z, the order-worker service in ap-southeast-2 experienced an interruption lasting
approximately 230 minutes. Checkout requests timed out for a subset of tenants.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `order-worker`
- Responsible team: Identity
- Severity: SEV-2
- Customer impact window: 230 minutes
- Tenant impact estimate: 15 tenants

## Timeline

- 2025-12-07T19:42:37Z — Alert fired; on-call engineer acknowledged the incident.
- 115 minutes later — Mitigation started and error rate began to fall.
- 230 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact032@example.com | +1-202-555-0132

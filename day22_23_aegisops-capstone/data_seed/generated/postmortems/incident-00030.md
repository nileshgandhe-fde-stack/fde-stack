# Post-mortem: identity-service incident INC-00030

## Summary

On 2026-11-16T05:57:33Z, the identity-service service in us-west-2 experienced an interruption lasting
approximately 180 minutes. Checkout requests timed out for a subset of tenants.

## Impact

- Affected service: `identity-service`
- Responsible team: Data Operations
- Severity: SEV-3
- Customer impact window: 180 minutes
- Tenant impact estimate: 32 tenants

## Timeline

- 2026-11-16T05:57:33Z — Alert fired; on-call engineer acknowledged the incident.
- 90 minutes later — Mitigation started and error rate began to fall.
- 180 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact040@example.com | +1-202-555-0140

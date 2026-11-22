# Post-mortem: identity-service incident INC-00041

## Summary

On 2026-08-12T16:18:29Z, the identity-service service in eu-west-1 experienced an interruption lasting
approximately 183 minutes. Checkout requests timed out for a subset of tenants.

## Impact

- Affected service: `identity-service`
- Responsible team: Identity
- Severity: SEV-1
- Customer impact window: 183 minutes
- Tenant impact estimate: 22 tenants

## Timeline

- 2026-08-12T16:18:29Z — Alert fired; on-call engineer acknowledged the incident.
- 91 minutes later — Mitigation started and error rate began to fall.
- 183 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact051@example.com | +1-202-555-0151

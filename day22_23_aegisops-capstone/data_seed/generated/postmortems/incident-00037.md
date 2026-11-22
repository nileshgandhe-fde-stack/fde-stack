# Post-mortem: identity-service incident INC-00037

## Summary

On 2025-12-03T23:09:59Z, the identity-service service in ap-southeast-2 experienced an interruption lasting
approximately 93 minutes. Checkout requests timed out for a subset of tenants.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `identity-service`
- Responsible team: Data Operations
- Severity: SEV-1
- Customer impact window: 93 minutes
- Tenant impact estimate: 34 tenants

## Timeline

- 2025-12-03T23:09:59Z — Alert fired; on-call engineer acknowledged the incident.
- 46 minutes later — Mitigation started and error rate began to fall.
- 93 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact047@example.com | +1-202-555-0147

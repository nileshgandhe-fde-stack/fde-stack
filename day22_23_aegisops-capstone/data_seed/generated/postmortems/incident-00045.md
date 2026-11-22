# Post-mortem: identity-service incident INC-00045

## Summary

On 2026-04-10T09:48:20Z, the identity-service service in ap-southeast-2 experienced an interruption lasting
approximately 138 minutes. Some users saw intermittent authentication failures.
Initial impact estimates were revised during review.

## Impact

- Affected service: `identity-service`
- Responsible team: Data Operations
- Severity: SEV-3
- Customer impact window: 138 minutes
- Tenant impact estimate: 28 tenants

## Timeline

- 2026-04-10T09:48:20Z — Alert fired; on-call engineer acknowledged the incident.
- 69 minutes later — Mitigation started and error rate began to fall.
- 138 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact055@example.com | +1-202-555-0155

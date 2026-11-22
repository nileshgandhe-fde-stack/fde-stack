# Post-mortem: identity-service incident INC-00019

## Summary

On 2026-02-25T00:49:26Z, the identity-service service in ap-southeast-2 experienced an interruption lasting
approximately 44 minutes. Background reconciliation fell behind its normal processing window.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `identity-service`
- Responsible team: Identity
- Severity: SEV-2
- Customer impact window: 44 minutes
- Tenant impact estimate: 34 tenants

## Timeline

- 2026-02-25T00:49:26Z — Alert fired; on-call engineer acknowledged the incident.
- 22 minutes later — Mitigation started and error rate began to fall.
- 44 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact029@example.com | +1-202-555-0129

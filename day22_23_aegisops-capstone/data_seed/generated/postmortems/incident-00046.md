# Post-mortem: identity-service incident INC-00046

## Summary

On 2026-02-11T20:26:18Z, the identity-service service in eu-west-1 experienced an interruption lasting
approximately 69 minutes. Background reconciliation fell behind its normal processing window.
Initial impact estimates were revised during review.

## Impact

- Affected service: `identity-service`
- Responsible team: Identity
- Severity: SEV-1
- Customer impact window: 69 minutes
- Tenant impact estimate: 5 tenants

## Timeline

- 2026-02-11T20:26:18Z — Alert fired; on-call engineer acknowledged the incident.
- 34 minutes later — Mitigation started and error rate began to fall.
- 69 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact056@example.com | +1-202-555-0156

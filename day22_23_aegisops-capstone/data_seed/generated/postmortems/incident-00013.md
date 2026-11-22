# Post-mortem: ledger-db incident INC-00013

## Summary

On 2026-05-20T15:55:28Z, the ledger-db service in eu-west-1 experienced an interruption lasting
approximately 70 minutes. Background reconciliation fell behind its normal processing window.
Initial impact estimates were revised during review.

## Impact

- Affected service: `ledger-db`
- Responsible team: Identity
- Severity: SEV-1
- Customer impact window: 70 minutes
- Tenant impact estimate: 18 tenants

## Timeline

- 2026-05-20T15:55:28Z — Alert fired; on-call engineer acknowledged the incident.
- 35 minutes later — Mitigation started and error rate began to fall.
- 70 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact023@example.com | +1-202-555-0123

# Post-mortem: ledger-db incident INC-00003

## Summary

On 2026-05-16T17:13:55Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 190 minutes. Read replicas returned stale data while the primary recovered.
Initial impact estimates were revised during review.

## Impact

- Affected service: `ledger-db`
- Responsible team: Platform
- Severity: SEV-2
- Customer impact window: 190 minutes
- Tenant impact estimate: 26 tenants

## Timeline

- 2026-05-16T17:13:55Z — Alert fired; on-call engineer acknowledged the incident.
- 95 minutes later — Mitigation started and error rate began to fall.
- 190 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact013@example.com | +1-202-555-0113

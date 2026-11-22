# Post-mortem: ledger-db incident INC-00035

## Summary

On 2026-05-01T08:07:33Z, the ledger-db service in eu-west-1 experienced an interruption lasting
approximately 198 minutes. Read replicas returned stale data while the primary recovered.
Initial impact estimates were revised during review.

## Impact

- Affected service: `ledger-db`
- Responsible team: Customer Experience
- Severity: SEV-2
- Customer impact window: 198 minutes
- Tenant impact estimate: 22 tenants

## Timeline

- 2026-05-01T08:07:33Z — Alert fired; on-call engineer acknowledged the incident.
- 99 minutes later — Mitigation started and error rate began to fall.
- 198 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact045@example.com | +1-202-555-0145

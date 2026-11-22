# Post-mortem: ledger-db incident INC-00049

## Summary

On 2026-11-21T03:32:03Z, the ledger-db service in eu-west-1 experienced an interruption lasting
approximately 189 minutes. Read replicas returned stale data while the primary recovered.
Initial impact estimates were revised during review.

## Impact

- Affected service: `ledger-db`
- Responsible team: Customer Experience
- Severity: SEV-1
- Customer impact window: 189 minutes
- Tenant impact estimate: 26 tenants

## Timeline

- 2026-11-21T03:32:03Z — Alert fired; on-call engineer acknowledged the incident.
- 94 minutes later — Mitigation started and error rate began to fall.
- 189 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact059@example.com | +1-202-555-0159

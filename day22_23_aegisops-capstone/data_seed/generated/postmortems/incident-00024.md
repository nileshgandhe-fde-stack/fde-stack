# Post-mortem: ledger-db incident INC-00024

## Summary

On 2026-05-15T05:00:04Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 111 minutes. Read replicas returned stale data while the primary recovered.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `ledger-db`
- Responsible team: Identity
- Severity: SEV-3
- Customer impact window: 111 minutes
- Tenant impact estimate: 23 tenants

## Timeline

- 2026-05-15T05:00:04Z — Alert fired; on-call engineer acknowledged the incident.
- 55 minutes later — Mitigation started and error rate began to fall.
- 111 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact034@example.com | +1-202-555-0134

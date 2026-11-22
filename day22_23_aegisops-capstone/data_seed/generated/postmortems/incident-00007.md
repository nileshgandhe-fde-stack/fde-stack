# Post-mortem: ledger-db incident INC-00007

## Summary

On 2026-02-27T07:48:35Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 28 minutes. Read replicas returned stale data while the primary recovered.

## Impact

- Affected service: `ledger-db`
- Responsible team: Customer Experience
- Severity: SEV-2
- Customer impact window: 28 minutes
- Tenant impact estimate: 12 tenants

## Timeline

- 2026-02-27T07:48:35Z — Alert fired; on-call engineer acknowledged the incident.
- 14 minutes later — Mitigation started and error rate began to fall.
- 28 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact017@example.com | +1-202-555-0117

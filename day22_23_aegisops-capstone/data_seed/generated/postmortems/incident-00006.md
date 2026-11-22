# Post-mortem: ledger-db incident INC-00006

## Summary

On 2026-04-19T05:18:43Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 101 minutes. Background reconciliation fell behind its normal processing window.

## Impact

- Affected service: `ledger-db`
- Responsible team: Platform
- Severity: SEV-3
- Customer impact window: 101 minutes
- Tenant impact estimate: 13 tenants

## Timeline

- 2026-04-19T05:18:43Z — Alert fired; on-call engineer acknowledged the incident.
- 50 minutes later — Mitigation started and error rate began to fall.
- 101 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact016@example.com | +1-202-555-0116

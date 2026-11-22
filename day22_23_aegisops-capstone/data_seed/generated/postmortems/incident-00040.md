# Post-mortem: ledger-db incident INC-00040

## Summary

On 2026-11-05T06:44:20Z, the ledger-db service in ap-southeast-2 experienced an interruption lasting
approximately 31 minutes. Checkout requests timed out for a subset of tenants.

## Impact

- Affected service: `ledger-db`
- Responsible team: Data Operations
- Severity: SEV-2
- Customer impact window: 31 minutes
- Tenant impact estimate: 14 tenants

## Timeline

- 2026-11-05T06:44:20Z — Alert fired; on-call engineer acknowledged the incident.
- 15 minutes later — Mitigation started and error rate began to fall.
- 31 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact050@example.com | +1-202-555-0150

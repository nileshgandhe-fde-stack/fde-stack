# Post-mortem: ledger-db incident INC-00029

## Summary

On 2025-11-22T07:16:48Z, the ledger-db service in us-west-2 experienced an interruption lasting
approximately 24 minutes. Checkout requests timed out for a subset of tenants.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `ledger-db`
- Responsible team: Identity
- Severity: SEV-3
- Customer impact window: 24 minutes
- Tenant impact estimate: 33 tenants

## Timeline

- 2025-11-22T07:16:48Z — Alert fired; on-call engineer acknowledged the incident.
- 12 minutes later — Mitigation started and error rate began to fall.
- 24 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact039@example.com | +1-202-555-0139

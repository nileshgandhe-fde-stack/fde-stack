# Post-mortem: ledger-db incident INC-00012

## Summary

On 2026-04-24T00:31:49Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 42 minutes. Checkout requests timed out for a subset of tenants.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `ledger-db`
- Responsible team: Customer Experience
- Severity: SEV-1
- Customer impact window: 42 minutes
- Tenant impact estimate: 11 tenants

## Timeline

- 2026-04-24T00:31:49Z — Alert fired; on-call engineer acknowledged the incident.
- 21 minutes later — Mitigation started and error rate began to fall.
- 42 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact022@example.com | +1-202-555-0122

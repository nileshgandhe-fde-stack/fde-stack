# Post-mortem: ledger-db incident INC-00014

## Summary

On 2026-04-17T15:51:08Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 42 minutes. Some users saw intermittent authentication failures.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `ledger-db`
- Responsible team: Payments
- Severity: SEV-3
- Customer impact window: 42 minutes
- Tenant impact estimate: 34 tenants

## Timeline

- 2026-04-17T15:51:08Z — Alert fired; on-call engineer acknowledged the incident.
- 21 minutes later — Mitigation started and error rate began to fall.
- 42 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact024@example.com | +1-202-555-0124

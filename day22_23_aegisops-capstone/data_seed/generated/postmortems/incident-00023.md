# Post-mortem: ledger-db incident INC-00023

## Summary

On 2025-12-31T10:12:19Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 45 minutes. Checkout requests timed out for a subset of tenants.

## Impact

- Affected service: `ledger-db`
- Responsible team: Platform
- Severity: SEV-3
- Customer impact window: 45 minutes
- Tenant impact estimate: 16 tenants

## Timeline

- 2025-12-31T10:12:19Z — Alert fired; on-call engineer acknowledged the incident.
- 22 minutes later — Mitigation started and error rate began to fall.
- 45 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact033@example.com | +1-202-555-0133

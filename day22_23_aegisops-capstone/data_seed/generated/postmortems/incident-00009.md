# Post-mortem: ledger-db incident INC-00009

## Summary

On 2026-06-22T21:09:10Z, the ledger-db service in eu-west-1 experienced an interruption lasting
approximately 128 minutes. Background reconciliation fell behind its normal processing window.

## Impact

- Affected service: `ledger-db`
- Responsible team: Platform
- Severity: SEV-1
- Customer impact window: 128 minutes
- Tenant impact estimate: 15 tenants

## Timeline

- 2026-06-22T21:09:10Z — Alert fired; on-call engineer acknowledged the incident.
- 64 minutes later — Mitigation started and error rate began to fall.
- 128 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact019@example.com | +1-202-555-0119

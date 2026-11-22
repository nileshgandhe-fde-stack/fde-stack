# Post-mortem: ledger-db incident INC-00016

## Summary

On 2026-06-05T11:43:01Z, the ledger-db service in us-west-2 experienced an interruption lasting
approximately 227 minutes. Background reconciliation fell behind its normal processing window.

## Impact

- Affected service: `ledger-db`
- Responsible team: Data Operations
- Severity: SEV-1
- Customer impact window: 227 minutes
- Tenant impact estimate: 7 tenants

## Timeline

- 2026-06-05T11:43:01Z — Alert fired; on-call engineer acknowledged the incident.
- 113 minutes later — Mitigation started and error rate began to fall.
- 227 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact026@example.com | +1-202-555-0126

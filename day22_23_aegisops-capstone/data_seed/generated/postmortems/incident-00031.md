# Post-mortem: ledger-db incident INC-00031

## Summary

On 2026-03-02T07:30:24Z, the ledger-db service in ap-southeast-2 experienced an interruption lasting
approximately 155 minutes. Some users saw intermittent authentication failures.
Initial impact estimates were revised during review.

## Impact

- Affected service: `ledger-db`
- Responsible team: Identity
- Severity: SEV-1
- Customer impact window: 155 minutes
- Tenant impact estimate: 45 tenants

## Timeline

- 2026-03-02T07:30:24Z — Alert fired; on-call engineer acknowledged the incident.
- 77 minutes later — Mitigation started and error rate began to fall.
- 155 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Taylor Kim | contact041@example.com | +1-202-555-0141

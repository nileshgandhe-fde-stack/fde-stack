# Post-mortem: ledger-db incident INC-00026

## Summary

On 2026-01-20T15:08:05Z, the ledger-db service in us-east-1 experienced an interruption lasting
approximately 219 minutes. Some users saw intermittent authentication failures.
Initial impact estimates were revised during review.

## Impact

- Affected service: `ledger-db`
- Responsible team: Customer Experience
- Severity: SEV-3
- Customer impact window: 219 minutes
- Tenant impact estimate: 31 tenants

## Timeline

- 2026-01-20T15:08:05Z — Alert fired; on-call engineer acknowledged the incident.
- 109 minutes later — Mitigation started and error rate began to fall.
- 219 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact036@example.com | +1-202-555-0136

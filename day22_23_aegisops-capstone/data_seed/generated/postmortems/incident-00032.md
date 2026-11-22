# Post-mortem: ledger-db incident INC-00032

## Summary

On 2026-10-01T04:13:16Z, the ledger-db service in eu-west-1 experienced an interruption lasting
approximately 160 minutes. Background reconciliation fell behind its normal processing window.

## Impact

- Affected service: `ledger-db`
- Responsible team: Customer Experience
- Severity: SEV-2
- Customer impact window: 160 minutes
- Tenant impact estimate: 33 tenants

## Timeline

- 2026-10-01T04:13:16Z — Alert fired; on-call engineer acknowledged the incident.
- 80 minutes later — Mitigation started and error rate began to fall.
- 160 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact042@example.com | +1-202-555-0142

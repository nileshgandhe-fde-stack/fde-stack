# Post-mortem: payments-api incident INC-00047

## Summary

On 2026-01-18T10:28:21Z, the payments-api service in us-east-1 experienced an interruption lasting
approximately 35 minutes. Background reconciliation fell behind its normal processing window.

## Impact

- Affected service: `payments-api`
- Responsible team: Customer Experience
- Severity: SEV-3
- Customer impact window: 35 minutes
- Tenant impact estimate: 7 tenants

## Timeline

- 2026-01-18T10:28:21Z — Alert fired; on-call engineer acknowledged the incident.
- 17 minutes later — Mitigation started and error rate began to fall.
- 35 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact057@example.com | +1-202-555-0157

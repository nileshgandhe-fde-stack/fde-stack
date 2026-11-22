# Post-mortem: payments-api incident INC-00028

## Summary

On 2026-01-12T17:06:18Z, the payments-api service in us-east-1 experienced an interruption lasting
approximately 57 minutes. Background reconciliation fell behind its normal processing window.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `payments-api`
- Responsible team: Identity
- Severity: SEV-1
- Customer impact window: 57 minutes
- Tenant impact estimate: 30 tenants

## Timeline

- 2026-01-12T17:06:18Z — Alert fired; on-call engineer acknowledged the incident.
- 28 minutes later — Mitigation started and error rate began to fall.
- 57 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact038@example.com | +1-202-555-0138

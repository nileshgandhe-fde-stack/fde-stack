# Post-mortem: payments-api incident INC-00042

## Summary

On 2025-12-07T10:17:24Z, the payments-api service in us-east-1 experienced an interruption lasting
approximately 165 minutes. Background reconciliation fell behind its normal processing window.

## Impact

- Affected service: `payments-api`
- Responsible team: Payments
- Severity: SEV-2
- Customer impact window: 165 minutes
- Tenant impact estimate: 34 tenants

## Timeline

- 2025-12-07T10:17:24Z — Alert fired; on-call engineer acknowledged the incident.
- 82 minutes later — Mitigation started and error rate began to fall.
- 165 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact052@example.com | +1-202-555-0152

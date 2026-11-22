# Post-mortem: customer-portal incident INC-00020

## Summary

On 2026-10-30T18:24:19Z, the customer-portal service in eu-west-1 experienced an interruption lasting
approximately 60 minutes. Background reconciliation fell behind its normal processing window.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `customer-portal`
- Responsible team: Data Operations
- Severity: SEV-1
- Customer impact window: 60 minutes
- Tenant impact estimate: 18 tenants

## Timeline

- 2026-10-30T18:24:19Z — Alert fired; on-call engineer acknowledged the incident.
- 30 minutes later — Mitigation started and error rate began to fall.
- 60 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact030@example.com | +1-202-555-0130

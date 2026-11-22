# Post-mortem: payments-api incident INC-00004

## Summary

On 2026-08-30T07:49:41Z, the payments-api service in ap-southeast-2 experienced an interruption lasting
approximately 122 minutes. Checkout requests timed out for a subset of tenants.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `payments-api`
- Responsible team: Data Operations
- Severity: SEV-2
- Customer impact window: 122 minutes
- Tenant impact estimate: 25 tenants

## Timeline

- 2026-08-30T07:49:41Z — Alert fired; on-call engineer acknowledged the incident.
- 61 minutes later — Mitigation started and error rate began to fall.
- 122 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact014@example.com | +1-202-555-0114

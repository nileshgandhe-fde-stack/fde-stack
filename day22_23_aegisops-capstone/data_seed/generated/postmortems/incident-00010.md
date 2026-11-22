# Post-mortem: payments-api incident INC-00010

## Summary

On 2026-03-06T13:40:06Z, the payments-api service in us-east-1 experienced an interruption lasting
approximately 217 minutes. Checkout requests timed out for a subset of tenants.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `payments-api`
- Responsible team: Payments
- Severity: SEV-3
- Customer impact window: 217 minutes
- Tenant impact estimate: 26 tenants

## Timeline

- 2026-03-06T13:40:06Z — Alert fired; on-call engineer acknowledged the incident.
- 108 minutes later — Mitigation started and error rate began to fall.
- 217 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact020@example.com | +1-202-555-0120

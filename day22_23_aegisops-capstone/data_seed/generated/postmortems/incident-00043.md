# Post-mortem: order-worker incident INC-00043

## Summary

On 2026-07-19T02:15:58Z, the order-worker service in eu-west-1 experienced an interruption lasting
approximately 222 minutes. Some users saw intermittent authentication failures.

## Impact

- Affected service: `order-worker`
- Responsible team: Customer Experience
- Severity: SEV-1
- Customer impact window: 222 minutes
- Tenant impact estimate: 32 tenants

## Timeline

- 2026-07-19T02:15:58Z — Alert fired; on-call engineer acknowledged the incident.
- 111 minutes later — Mitigation started and error rate began to fall.
- 222 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact053@example.com | +1-202-555-0153

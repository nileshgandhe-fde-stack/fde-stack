# Post-mortem: order-worker incident INC-00005

## Summary

On 2026-05-26T22:13:31Z, the order-worker service in eu-west-1 experienced an interruption lasting
approximately 48 minutes. Background reconciliation fell behind its normal processing window.
Initial impact estimates were revised during review.

## Impact

- Affected service: `order-worker`
- Responsible team: Identity
- Severity: SEV-3
- Customer impact window: 48 minutes
- Tenant impact estimate: 36 tenants

## Timeline

- 2026-05-26T22:13:31Z — Alert fired; on-call engineer acknowledged the incident.
- 24 minutes later — Mitigation started and error rate began to fall.
- 48 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact015@example.com | +1-202-555-0115

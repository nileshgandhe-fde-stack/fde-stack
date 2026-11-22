# Post-mortem: identity-service incident INC-00034

## Summary

On 2026-10-16T01:11:45Z, the identity-service service in us-west-2 experienced an interruption lasting
approximately 208 minutes. Background reconciliation fell behind its normal processing window.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `identity-service`
- Responsible team: Customer Experience
- Severity: SEV-1
- Customer impact window: 208 minutes
- Tenant impact estimate: 9 tenants

## Timeline

- 2026-10-16T01:11:45Z — Alert fired; on-call engineer acknowledged the incident.
- 104 minutes later — Mitigation started and error rate began to fall.
- 208 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact044@example.com | +1-202-555-0144

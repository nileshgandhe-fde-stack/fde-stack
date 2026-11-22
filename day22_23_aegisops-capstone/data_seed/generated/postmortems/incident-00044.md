# Post-mortem: order-worker incident INC-00044

## Summary

On 2026-06-02T20:55:24Z, the order-worker service in us-east-1 experienced an interruption lasting
approximately 163 minutes. Some users saw intermittent authentication failures.

## Impact

- Affected service: `order-worker`
- Responsible team: Platform
- Severity: SEV-2
- Customer impact window: 163 minutes
- Tenant impact estimate: 24 tenants

## Timeline

- 2026-06-02T20:55:24Z — Alert fired; on-call engineer acknowledged the incident.
- 81 minutes later — Mitigation started and error rate began to fall.
- 163 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Jordan Lee | contact054@example.com | +1-202-555-0154

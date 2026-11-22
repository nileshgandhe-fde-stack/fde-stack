# Post-mortem: customer-portal incident INC-00015

## Summary

On 2026-11-02T06:08:38Z, the customer-portal service in ap-southeast-2 experienced an interruption lasting
approximately 142 minutes. Some users saw intermittent authentication failures.
Initial impact estimates were revised during review.

## Impact

- Affected service: `customer-portal`
- Responsible team: Customer Experience
- Severity: SEV-3
- Customer impact window: 142 minutes
- Tenant impact estimate: 28 tenants

## Timeline

- 2026-11-02T06:08:38Z — Alert fired; on-call engineer acknowledged the incident.
- 71 minutes later — Mitigation started and error rate began to fall.
- 142 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact025@example.com | +1-202-555-0125

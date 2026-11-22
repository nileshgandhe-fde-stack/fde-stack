# Post-mortem: identity-service incident INC-00011

## Summary

On 2026-02-25T11:35:14Z, the identity-service service in us-west-2 experienced an interruption lasting
approximately 209 minutes. Some users saw intermittent authentication failures.

## Impact

- Affected service: `identity-service`
- Responsible team: Platform
- Severity: SEV-2
- Customer impact window: 209 minutes
- Tenant impact estimate: 35 tenants

## Timeline

- 2026-02-25T11:35:14Z — Alert fired; on-call engineer acknowledged the incident.
- 104 minutes later — Mitigation started and error rate began to fall.
- 209 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact021@example.com | +1-202-555-0121

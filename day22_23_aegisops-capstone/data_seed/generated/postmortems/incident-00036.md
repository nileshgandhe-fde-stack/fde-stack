# Post-mortem: identity-service incident INC-00036

## Summary

On 2026-11-17T15:24:09Z, the identity-service service in ap-southeast-2 experienced an interruption lasting
approximately 177 minutes. Some users saw intermittent authentication failures.

## Impact

- Affected service: `identity-service`
- Responsible team: Platform
- Severity: SEV-2
- Customer impact window: 177 minutes
- Tenant impact estimate: 28 tenants

## Timeline

- 2026-11-17T15:24:09Z — Alert fired; on-call engineer acknowledged the incident.
- 88 minutes later — Mitigation started and error rate began to fall.
- 177 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact046@example.com | +1-202-555-0146

# Post-mortem: identity-service incident INC-00039

## Summary

On 2026-07-10T13:18:48Z, the identity-service service in eu-west-1 experienced an interruption lasting
approximately 104 minutes. Checkout requests timed out for a subset of tenants.

## Impact

- Affected service: `identity-service`
- Responsible team: Customer Experience
- Severity: SEV-1
- Customer impact window: 104 minutes
- Tenant impact estimate: 3 tenants

## Timeline

- 2026-07-10T13:18:48Z — Alert fired; on-call engineer acknowledged the incident.
- 52 minutes later — Mitigation started and error rate began to fall.
- 104 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact049@example.com | +1-202-555-0149

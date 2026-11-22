# Post-mortem: customer-portal incident INC-00050

## Summary

On 2025-12-17T17:40:33Z, the customer-portal service in eu-west-1 experienced an interruption lasting
approximately 20 minutes. Some users saw intermittent authentication failures.
A few timestamps in the source ticket were approximate.

## Impact

- Affected service: `customer-portal`
- Responsible team: Platform
- Severity: SEV-1
- Customer impact window: 20 minutes
- Tenant impact estimate: 34 tenants

## Timeline

- 2025-12-17T17:40:33Z — Alert fired; on-call engineer acknowledged the incident.
- 10 minutes later — Mitigation started and error rate began to fall.
- 20 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A dependency slowdown caused retries to amplify queue load.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact060@example.com | +1-202-555-0160

# Post-mortem: customer-portal incident INC-00001

## Summary

On 2026-04-15T22:14:40Z, the customer-portal service in us-west-2 experienced an interruption lasting
approximately 44 minutes. Read replicas returned stale data while the primary recovered.

## Impact

- Affected service: `customer-portal`
- Responsible team: Data Operations
- Severity: SEV-2
- Customer impact window: 44 minutes
- Tenant impact estimate: 16 tenants

## Timeline

- 2026-04-15T22:14:40Z — Alert fired; on-call engineer acknowledged the incident.
- 22 minutes later — Mitigation started and error rate began to fall.
- 44 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A recent deployment increased connection pool pressure.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Alex Morgan | contact011@example.com | +1-202-555-0111

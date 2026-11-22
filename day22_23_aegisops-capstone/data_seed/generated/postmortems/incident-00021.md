# Post-mortem: payments-api incident INC-00021

## Summary

On 2025-12-12T17:06:13Z, the payments-api service in eu-west-1 experienced an interruption lasting
approximately 97 minutes. Read replicas returned stale data while the primary recovered.
Initial impact estimates were revised during review.

## Impact

- Affected service: `payments-api`
- Responsible team: Identity
- Severity: SEV-2
- Customer impact window: 97 minutes
- Tenant impact estimate: 7 tenants

## Timeline

- 2025-12-12T17:06:13Z — Alert fired; on-call engineer acknowledged the incident.
- 48 minutes later — Mitigation started and error rate began to fall.
- 97 minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

A configuration drift reduced available worker capacity.
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

Casey Patel | contact031@example.com | +1-202-555-0131

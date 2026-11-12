# Payments Service Runbook

Use this runbook to triage payment API availability and payment authorization issues.
Follow the incident process for your environment and avoid sharing payment or customer
data in logs or incident channels.

## TLS Errors

### `ERR_SSL_09`

1. Check the payment service health dashboard and the current TLS certificate expiry.
2. Verify the configured certificate and hostname for the affected endpoint.
3. If a certificate is expired or mismatched, follow the approved certificate
   renewal and deployment procedure.
4. Confirm the endpoint health check succeeds after the change. Escalate to the
   platform on-call if the issue persists.

### Other TLS Handshake Failures

Compare the failure time and affected endpoint with recent certificate, load balancer,
or TLS policy changes. Do not disable certificate validation as a workaround.

## Payment Authorization Failures

Check the payment provider status page and the service's dependency health metrics.
Use request IDs to correlate application and provider logs, and redact tokens and
payment details before sharing log excerpts.

If failures began after a deployment, follow the service's approved rollback procedure
and notify the incident commander.

## Database Connection Pool

Review database connection usage, pool saturation, and connection timeout metrics.
Check for recent traffic changes or slow database operations before changing pool
limits. Escalate capacity or configuration changes to the database on-call.

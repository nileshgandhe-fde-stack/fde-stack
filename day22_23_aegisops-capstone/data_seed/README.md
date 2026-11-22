# Seed Data

`seed_enterprise_data.py` generates synthetic operational data without external
services. Run it from the repository root to create:

- 1,000 PagerDuty/Prometheus JSON alert records in `generated/alerts.jsonl`
- 50 Markdown incident post-mortems in `generated/postmortems/`
- 10,000 tenant SLA records in `generated/tenant_sla.csv`
- operational Markdown runbooks in `runbooks/`

Use `--seed` together with `--as-of 2026-01-01T00:00:00Z` to make all output
reproducible. Output files are written under `generated/` by default and are
excluded from version control.

Runbooks are available to all three UI roles. Post-mortems must be redacted
before indexing and are restricted to the SRE Lead role.
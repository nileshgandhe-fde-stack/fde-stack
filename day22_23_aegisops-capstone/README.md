# AegisOps Capstone Storage Demo

This folder contains `aegis_storage.py`, a small Python demonstration of tenant
SLA analytics and role-filtered runbook search. It uses an in-memory DuckDB
database with seeded sample data; it does not connect to a live service or
persist data between runs.

## Requirements and running

Python 3 and the `duckdb` package are required. From the repository root, run:

```bash
python3 day22_23_aegisops-capstone/aegis_storage.py
```

The script prints an SLA summary, performs a sample runbook search as
`ops_viewer`, and displays the PII-redaction and RBAC-block counters.

## `AegisOpsCoreEngine`

Creating an engine opens a DuckDB in-memory connection, seeds the
`tenant_sla_events` table and three governed runbooks, and initializes two
counters:

- `pii_redacted_total` counts email addresses and SSN-shaped values replaced by
  the PII scrubber.
- `rbac_blocks_total` counts runbooks denied to the supplied caller role during
  searches.

### SLA analytics

`query_sla_summary()` groups the five seeded incidents by tenant and returns a
Pandas DataFrame with:

- incident count and number of SLA breaches;
- average MTTR in minutes, rounded to one decimal place;
- peak recorded p95 latency in milliseconds.

For the current sample data, the summary includes two breached incidents for
`acme_health`, one for `globex_fin`, and none for `initech_supply`.

### PII scrubbing and runbook search

`scrub_pii(text)` replaces email-like strings with `<REDACTED_EMAIL>` and
values matching the `NNN-NN-NNNN` pattern with `<REDACTED_SSN>`. The redaction
counter increases for each match.

`search_runbooks(query, caller_role)` scrubs and lowercases the query, then
checks each runbook's `allowed_roles` before matching. A caller without
permission cannot receive that runbook, and each denied runbook increments
`rbac_blocks_total`. For permitted runbooks, a result is included if any
whitespace-separated query token longer than two characters occurs in the
runbook title or body (case-insensitive). The method returns a list of matching
runbook dictionaries.

The seeded roles demonstrate progressively restricted access:

| Runbook | Allowed roles |
| --- | --- |
| `RB-101` — HL7 FHIR Gateway Connection Pool Exhaustion | `ops_viewer`, `sec_auditor`, `fde_admin` |
| `RB-102` — SWIFT Wire API Mutual-TLS Certificate Rotation Runbook | `sec_auditor`, `fde_admin` |
| `RB-999` — Executive-only SOC2 findings | `fde_admin` |

## Example

The script's sample search uses the `ops_viewer` role and a query containing
HL7 and SOC2 terms, an email address, and an SSN-shaped value. The search
returns the matching `RB-101` runbook, redacts two PII matches, and counts two
runbooks blocked by role.

You can also use the engine from Python:

From this folder, start Python and use:

```python
from aegis_storage import AegisOpsCoreEngine

engine = AegisOpsCoreEngine()
summary = engine.query_sla_summary()
runbooks = engine.search_runbooks("hl7 gateway", caller_role="ops_viewer")
```

## Scope and limitations

This is an illustrative, local demo rather than a production security or
storage layer. DuckDB data and counters exist only for the lifetime of the
engine. PII detection covers only the two regular-expression patterns above,
and `caller_role` is a method argument—not an authenticated identity or an
authorization system.

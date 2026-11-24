# day 22-23: Capstone Phase 1: 'AegisOps' Ingestion & Storage Core 
# day 24-25: Capstone Phase 2: Governed Copilot API & SRE Telemetry
# AegisOps FDE Platform


A role-aware incident assistant combining read-only DuckDB SLA metrics,
Markdown runbooks, and (when configured) redacted post-mortems from Neon
pgvector. The FastAPI backend builds its incident-analysis workflow with
LangGraph; the Streamlit UI includes role switching and an SRE control plane.

## Local demo

Install the project and test dependencies, then generate seed data and load the
local metrics database:

```sh
python -m pip install -e ".[test]"
python data_seed/seed_enterprise_data.py
python -c "from aegisops.ingestion import DuckDBSlaStore; store = DuckDBSlaStore('data_seed/generated/aegisops.duckdb'); store.load_csv('data_seed/generated/tenant_sla.csv'); store.close()"
```

Create a `.env` file in the repository root with your local settings. Keep the
file private; it is ignored by Git. Demo role issuance is disabled unless
explicitly enabled:

```sh
JWT_SECRET=replace-with-a-private-random-secret-at-least-32-bytes-long
DEMO_TOKEN_ISSUER_ENABLED=true
OPENAI_API_KEY=your-openai-api-key
```

Start the API from the repository root:

```sh
PYTHONPATH=backend uvicorn --env-file .env aegisops.api:app --reload --port 8000
```

In another terminal, start the UI:

```sh
streamlit run ui/app.py
```

The demo issuer can mint all three demonstration roles and is not an identity
provider. Keep it disabled outside a controlled, isolated demo. Before
production, replace the demo HS256 issuer and validator with the organization's
identity-provider integration and trusted signing keys. Point `AEGISOPS_API_URL`
at the API if it is not at `http://localhost:8000`.

To enable semantic post-mortem retrieval, set `POSTMORTEM_DATABASE_URL` to a
read-only connection for the already-ingested, PII-redacted pgvector index and
provide the embedding settings used during ingestion. The API combines these
SRE-only results with local Markdown runbooks. The API's `/metrics` endpoint
exports Prometheus metrics; restrict it to trusted monitoring networks.

Run tests with `python -m pytest`.
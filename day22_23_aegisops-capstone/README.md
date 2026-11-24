# AegisOps FDE Platform

AegisOps is a role-aware incident assistant for operational teams. Its FastAPI
backend queries SLA data from DuckDB in read-only mode, retrieves Markdown
runbooks, and can retrieve redacted post-mortems from Neon pgvector. An
An OpenAI-compatible chat service powers analysis; embeddings enable optional
semantic retrieval. The Streamlit UI provides incident analysis, a demo role
switcher, and an SRE control plane.

## Features

- Role-scoped incident analysis for SRE Lead, Tier-1 Support, and External
  Auditor demo roles.
- Read-only SLA queries, runbook retrieval, and optional semantic retrieval of
  PII-redacted post-mortems.
- SRE telemetry for API p95 latency, estimated LLM cost, circuit-breaker
  status, and PII redaction counts.
- Prometheus metrics at `/metrics` and a health endpoint at `/health`.

## Live demo

[Open the Streamlit UI](https://fde-stack.onrender.com/). The UI requires a
reachable AegisOps API; see [Deploy to Render](#deploy-to-render-free-tier).

## Run locally

Use Python 3.11 or newer from the project directory:

```sh
python -m pip install -e ".[test]"
python data_seed/seed_enterprise_data.py
python -c "from aegisops.ingestion import DuckDBSlaStore; store = DuckDBSlaStore('data_seed/generated/aegisops.duckdb'); store.load_csv('data_seed/generated/tenant_sla.csv'); store.close()"
```

Create a private `.env` file in the project directory. Do not commit secrets:

```dotenv
JWT_SECRET=replace-with-a-private-random-secret-at-least-32-bytes-long
DEMO_TOKEN_ISSUER_ENABLED=true
OPENAI_API_KEY=your-provider-api-key
# Optional: set this to an OpenAI-compatible provider endpoint/model.
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_CHAT_MODEL=gpt-4o-mini
```

Start the API from the project directory:

```sh
PYTHONPATH=backend uvicorn --env-file .env aegisops.api:app --reload --port 8000
```

In another terminal, start the UI:

```sh
streamlit run ui/app.py
```

The UI defaults to `http://localhost:8000`. Set `AEGISOPS_API_URL` if the API
uses another address. For local runbook retrieval, the repository's runbooks
are in `data_seed/runbook`; set `RUNBOOKS_DIR=data_seed/runbook` if using that
directory.

The demo JWT issuer is not an identity provider. Keep it disabled except for a
controlled demo; use an organization's identity provider and trusted signing
keys for production. The API requires a `JWT_SECRET` of at least 32 bytes.
Incident synthesis requires an LLM API key. To enable semantic post-mortem
retrieval, configure `POSTMORTEM_DATABASE_URL` with a read-only connection to
an already-ingested, PII-redacted pgvector index, plus the embedding model and
dimensions used to create that index. Restrict `/metrics` to trusted
monitoring systems.

Run the test suite from the project directory:

```sh
python -m pytest
```

## Deploy to Render (Free tier)

The existing Render URL hosts the Streamlit UI. For incident analysis and the
control plane to work, deploy the FastAPI backend as a second Render Web
Service and configure the UI to use its public URL. Render Free services can
spin down when idle, so the first request after inactivity may take longer.

### 1. Deploy the API

1. In the [Render Dashboard](https://dashboard.render.com/), create a **New
   Web Service** and connect this GitHub repository.
2. Set **Root Directory** to `day22_23_aegisops-capstone`.
3. Select the **Python** runtime and the **Free** instance type.
4. Set the build command to:

   ```sh
   python -m pip install .
   ```

5. Set the start command to:

   ```sh
   PYTHONPATH=backend uvicorn aegisops.api:app --host 0.0.0.0 --port $PORT
   ```

6. Add the following environment variables in Render. Generate a unique,
   private `JWT_SECRET` with at least 32 bytes; enter secrets in the Render
   Dashboard, not in source control.

   | Key | Value |
   | --- | --- |
   | `JWT_SECRET` | A private random secret, at least 32 bytes |
   | `DEMO_TOKEN_ISSUER_ENABLED` | `true` for the public demo only |
   | `OPENAI_API_KEY` | API key for the configured OpenAI-compatible provider |
   | `RUNBOOKS_DIR` | `data_seed/runbook` |

   The deployed demo database defaults to
   `data_seed/generated/aegisops.duckdb`. If you use another database, set
   `DUCKDB_PATH` accordingly. Set `OPENAI_BASE_URL` and `OPENAI_CHAT_MODEL` if
   using a provider other than the defaults. Configure `POSTMORTEM_DATABASE_URL`
   and the matching embedding settings only when using a populated, redacted
   pgvector index.
7. Deploy the service and verify its health endpoint at
   `https://<your-api-service>.onrender.com/health`. It should return
   `{"status":"ok"}`. Copy the service's public URL for the UI configuration.

### 2. Deploy or update the Streamlit UI

1. Create a second **Web Service** from the same repository (or open the
   existing UI service).
2. Set **Root Directory** to `day22_23_aegisops-capstone`, select **Docker**
   as the runtime, and choose the **Free** instance type. Render will build
   the service from the repository's `Dockerfile`.
3. The current Dockerfile starts Streamlit on port `7860`. Configure the
   service's web port/`PORT` as `7860` so Render routes traffic to the port
   Streamlit listens on.
4. Add the environment variable `AEGISOPS_API_URL` with the public URL of the
   API service from step 1 (for example,
   `https://<your-api-service>.onrender.com`).
5. Deploy the service. Open its `onrender.com` URL, mint a demo JWT, and try
   an incident question. The SRE Control Plane also requires a minted token.

Keep the demo token issuer enabled only for a controlled demonstration.
Anyone who can reach the public demo can request a demo role token; do not use
this configuration to protect production data or services.

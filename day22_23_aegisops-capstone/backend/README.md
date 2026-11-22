# Backend

FastAPI incident assistant and ingestion/storage services.

Install the project and test dependencies into the active environment from the
repository root with `python -m pip install -e ".[test]"`. Run the test suite
with `python -m pytest` (do not execute the test file directly). Generate seed
data with `python data_seed/seed_enterprise_data.py`.

```sh
PYTHONPATH=backend uvicorn aegisops.api:app --reload
```

The API reads `sla_metrics` from `DUCKDB_PATH` (default
`data_seed/generated/aegisops.duckdb`) in read-only mode. Markdown runbooks are
read from `RUNBOOKS_DIR` (default `data_seed/runbooks`). To enable SRE-only
semantic post-mortem retrieval, configure `POSTMORTEM_DATABASE_URL` with a
read-only pgvector connection to the index populated by ingestion. This index
contains redacted text; local post-mortem overrides must be pre-redacted and
configured through `REDACTED_POSTMORTEMS_DIR`.

`JWT_SECRET` must be at least 32 bytes. Demo JWT issuance is disabled by default
and is only for isolated demonstrations; enable it with
`DEMO_TOKEN_ISSUER_ENABLED=true`. A production deployment must use a trusted
identity provider and must not expose the demo issuer.

`OPENAI_API_KEY` and `OPENAI_CHAT_MODEL` configure synthesis;
`OPENAI_BASE_URL` selects an OpenAI-compatible service.
`OPENAI_EMBEDDING_MODEL` and `OPENAI_EMBEDDING_DIMENSIONS` configure semantic
retrieval and must match ingestion. Set `LLM_INPUT_COST_PER_1M` and
`LLM_OUTPUT_COST_PER_1M` for estimated control-plane cost reporting.

The API exports Prometheus metrics at `/metrics`, including instrumented HTTP
latency and AegisOps LLM, circuit-breaker, and PII-redaction counters.
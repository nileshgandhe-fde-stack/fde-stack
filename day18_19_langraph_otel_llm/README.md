# LangGraph SRE Agent with Phoenix

This example routes requests through a deterministic LangGraph:

1. `IntentRouter` selects analytics or runbook retrieval.
2. `SafeSQLTool` runs a fixed, parameterized `SELECT` against DuckDB or Postgres. It never accepts SQL from the caller.
3. `RunbookRAGTool` ranks sections from the local payment runbook using deterministic term overlap.
4. `HallucinationGrader` checks answer/context token overlap and can rewrite and retry once. If evidence is still missing, it abstains.

The FastAPI endpoints are `/api/v1/ask` and `/api/v1/ask/stream`. OpenTelemetry instruments FastAPI and OpenInference instruments LangGraph/LangChain. Request traces include `tenant.id`, `fde.ttft_ms`, `fde.token_count.prompt`, `fde.token_count.completion`, `fde.token_cost_usd`, and `fde.tool_latency_ms`. Token counts are estimates, and cost defaults to zero because this demo does not call a paid language model. Set `INPUT_COST_PER_1M_TOKENS` and `OUTPUT_COST_PER_1M_TOKENS` to calculate estimates.

## Run locally

Start Phoenix:

```bash
docker run -d --name fde-phoenix \
  -e PHOENIX_ENABLE_AUTH=false \
  -p 127.0.0.1:6006:6006 \
  arizephoenix/phoenix
```

Install the example dependencies and start the API:

```bash
python -m pip install -r day18_19_langraph_otel_llm/requirements.txt
uvicorn day18_19_langraph_otel_llm.agent_with_sre_evals:app --host 0.0.0.0 --port 8000
```

Phoenix is available at [http://localhost:6006](http://localhost:6006). The exporter sends traces to `http://localhost:6006/v1/traces`; override it with `PHOENIX_COLLECTOR_ENDPOINT`.

Generate a trace:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H 'content-type: application/json' \
  -d '{"query":"How many SLA breaches did acme_health have this week?","tenant_id":"acme_health"}'
```

Generate a streamed trace with a tenant tag:

```bash
curl -N -X POST http://localhost:8000/api/v1/ask/stream \
  -H 'content-type: application/json' \
  -d '{"query":"What should I check for ERR_SSL_09?","tenant_id":"acme_health"}'
```

In Phoenix, open **Projects → `fde-sre-agent` → Traces**, then select a `fde.ask` or `fde.ask.stream` trace. The request span includes tenant, TTFT, token-count, token-cost, and tool-latency attributes; `SafeSQLTool.execute` and `RunbookRAGTool.retrieve` child spans include individual tool latency.

To print recent request and tool spans from the terminal (using the Python environment where the dependencies are installed):

```bash
python - <<'PY'
from phoenix.client import Client

spans = Client(base_url="http://localhost:6006").spans.get_spans_dataframe(
    project_name="fde-sre-agent",
    limit=100,
)
names = [
    "fde.ask",
    "fde.ask.stream",
    "SafeSQLTool.execute",
    "RunbookRAGTool.retrieve",
]
columns = [
    column
    for column in (
        "name",
        "start_time",
        "latency_ms",
        "attributes.tenant",
        "attributes.fde",
        "attributes.llm.token_count.prompt",
        "attributes.llm.token_count.completion",
        "attributes.llm.cost.total",
        "attributes.tool_latency_ms",
    )
    if column in spans.columns
]
print(spans[spans["name"].isin(names)][columns].to_string(index=False))
PY
```

## Read-only data configuration

Without `DATABASE_URL`, the agent uses an in-memory DuckDB database seeded with sample `sre_metrics` rows. To use a DuckDB file, set `DUCKDB_PATH` to an existing database containing the `sre_metrics` table; the file opens read-only.

For Postgres, set `DATABASE_URL` to a connection string and create a readable `sre_metrics` table with `tenant_id`, `metric`, `value`, and `period` columns. Connections enforce `default_transaction_read_only=on`. A supplied `tenant_id` limits results; omit it to query all tenants.

The SQL is selected by the application and is never constructed from raw caller SQL. For custom runbooks, set `RUNBOOK_PATH` to a Markdown file.

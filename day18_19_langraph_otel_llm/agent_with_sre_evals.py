import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

import duckdb
import psycopg
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langgraph.graph import END, START, StateGraph
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool


class GraphState(TypedDict, total=False):
    query: str
    original_query: str
    caller_role: str
    tenant_id: str
    intent: str
    retrieved_context: str
    draft_answer: str
    grounded_score: float
    rewrite_count: int
    retry_requested: bool
    telemetry: dict[str, Any]


@dataclass
class AgentState:
    query: str
    caller_role: str
    tenant_id: str = ""
    rewritten_query: str = ""
    intent: str = ""
    retrieved_context: str = ""
    draft_answer: str = ""
    grounded_score: float = 0.0
    rewrite_count: int = 0
    telemetry: dict[str, Any] = field(default_factory=dict)


_SQL_KEYWORDS = (
    "how many",
    "count",
    "breach",
    "average",
    "top",
    "sla",
    "latency",
    "metric",
    "metrics",
)
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "with",
    "code", "evidence", "incident", "lookup", "metrics", "read", "remediation",
    "request", "runbook", "search", "steps",
}
_TRACER = trace.get_tracer("fde-stack.agent")
_DUCKDB_LOCK = threading.Lock()
_DUCKDB_CONNECTION: duckdb.DuckDBPyConnection | None = None


def _configure_telemetry() -> None:
    provider = register(
        project_name=os.getenv("PHOENIX_PROJECT_NAME", "fde-sre-agent"),
        endpoint=os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"
        ),
    )
    LangChainInstrumentor().instrument(tracer_provider=provider)


def _duckdb_connection() -> duckdb.DuckDBPyConnection:
    global _DUCKDB_CONNECTION
    if _DUCKDB_CONNECTION is None:
        path = os.getenv("DUCKDB_PATH", ":memory:")
        connection = duckdb.connect(path, read_only=path != ":memory:")
        if path == ":memory:":
            connection.execute(
                """
                CREATE TABLE sre_metrics (
                    tenant_id VARCHAR,
                    metric VARCHAR,
                    value DOUBLE,
                    period VARCHAR
                )
                """
            )
            connection.executemany(
                "INSERT INTO sre_metrics VALUES (?, ?, ?, ?)",
                [
                    ("acme_health", "sla_breaches", 3, "this_week"),
                    ("acme_health", "p95_latency_ms", 1420, "this_week"),
                    ("northstar", "sla_breaches", 0, "this_week"),
                    ("northstar", "p95_latency_ms", 310, "this_week"),
                ],
            )
        _DUCKDB_CONNECTION = connection
    return _DUCKDB_CONNECTION


def _execute_readonly_metrics_query(tenant_id: str) -> list[tuple[Any, ...]]:
    filter_by_tenant = bool(tenant_id)
    if os.getenv("DATABASE_URL"):
        where_clause = " WHERE tenant_id = %s" if filter_by_tenant else ""
        sql = (
            "SELECT tenant_id, metric, value, period FROM sre_metrics"
            f"{where_clause} ORDER BY tenant_id, metric LIMIT 100"
        )
        with psycopg.connect(
            os.environ["DATABASE_URL"],
            options="-c default_transaction_read_only=on",
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (tenant_id,) if filter_by_tenant else ())
                return cursor.fetchall()

    where_clause = " WHERE tenant_id = ?" if filter_by_tenant else ""
    sql = (
        "SELECT tenant_id, metric, value, period FROM sre_metrics"
        f"{where_clause} ORDER BY tenant_id, metric LIMIT 100"
    )
    with _DUCKDB_LOCK:
        connection = _duckdb_connection()
        result = connection.execute(
            sql, [tenant_id] if filter_by_tenant else []
        ).fetchall()
    return result


def node_intent_router(state: GraphState) -> dict[str, str]:
    query = state["query"].lower()
    intent = (
        "SQL_ANALYTICS"
        if any(keyword in query for keyword in _SQL_KEYWORDS)
        else "RUNBOOK_RAG"
    )
    return {"intent": intent}


def node_safe_sql_tool(state: GraphState) -> dict[str, Any]:
    started = time.perf_counter()
    with _TRACER.start_as_current_span("SafeSQLTool.execute") as span:
        span.set_attribute("tool.name", "SafeSQLTool")
        rows = _execute_readonly_metrics_query(state.get("tenant_id", ""))
        context = "\n".join(
            f"tenant_id={tenant_id} metric={metric} value={value:g} period={period}"
            for tenant_id, metric, value, period in rows
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        span.set_attribute("tool_latency_ms", latency_ms)

    telemetry = dict(state.get("telemetry", {}))
    telemetry["tool_latency_ms"] = latency_ms
    return {
        "retrieved_context": context,
        "draft_answer": context,
        "telemetry": telemetry,
    }


def _runbook_sections() -> list[str]:
    configured_path = os.getenv("RUNBOOK_PATH")
    runbook_path = (
        Path(configured_path)
        if configured_path
        else Path(__file__).parent.parent
        / "day15_16_hybrid_search_rag"
        / "paymentrunbook.md"
    )
    return [
        section.strip()
        for section in re.split(r"(?m)(?=^#{2,3} )", runbook_path.read_text())
        if section.strip()
    ]


def node_runbook_rag_tool(state: GraphState) -> dict[str, Any]:
    started = time.perf_counter()
    with _TRACER.start_as_current_span("RunbookRAGTool.retrieve") as span:
        span.set_attribute("tool.name", "RunbookRAGTool")
        query_terms = {
            term
            for term in re.findall(r"[a-z0-9_]+", state["query"].lower())
            if term not in _STOP_WORDS and len(term) > 1
        }
        ranked_sections = sorted(
            (
                (
                    len(
                        query_terms
                        & set(re.findall(r"[a-z0-9_]+", section.lower()))
                    ),
                    section,
                )
                for section in _runbook_sections()
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        context = ranked_sections[0][1] if ranked_sections and ranked_sections[0][0] else ""
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        span.set_attribute("tool_latency_ms", latency_ms)

    telemetry = dict(state.get("telemetry", {}))
    telemetry["tool_latency_ms"] = latency_ms
    return {
        "retrieved_context": context,
        "draft_answer": context,
        "telemetry": telemetry,
    }


def _rewrite_query(state: GraphState) -> str:
    if state["intent"] == "SQL_ANALYTICS":
        tenant = state.get("tenant_id", "") or "all tenants"
        return (
            f"Read-only SRE metrics for {tenant}; clarify this request: "
            f"{state['query']}"
        )
    terms = re.findall(r"ERR_[A-Za-z0-9_]+|[A-Za-z0-9_-]+", state["query"])
    subject = " ".join(terms) or state["query"]
    return f"Runbook evidence and remediation steps for: {subject}"


def node_hallucination_grader(state: GraphState) -> dict[str, Any]:
    context_tokens = set(re.findall(r"[a-z0-9_]+", state["retrieved_context"].lower()))
    answer_tokens = [
        token
        for token in re.findall(r"[a-z0-9_]+", state["draft_answer"].lower())
        if token not in _STOP_WORDS
    ]
    matched = sum(token in context_tokens for token in answer_tokens)
    score = round(matched / len(answer_tokens), 2) if answer_tokens else 0.0
    retry_requested = score < 0.5 and state.get("rewrite_count", 0) < 1
    telemetry = dict(state.get("telemetry", {}))
    telemetry["faithfulness_sli"] = score
    telemetry["slo_pass"] = score >= 0.5

    update: dict[str, Any] = {
        "grounded_score": score,
        "telemetry": telemetry,
        "retry_requested": retry_requested,
    }
    if retry_requested:
        update["query"] = _rewrite_query(state)
        update["rewrite_count"] = state.get("rewrite_count", 0) + 1
    elif score < 0.5:
        update["draft_answer"] = (
            "I could not ground an answer in the retrieved context."
        )
    return update


def _after_grading(state: GraphState) -> str:
    return "IntentRouter" if state.get("retry_requested", False) else END


def _build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("IntentRouter", node_intent_router)
    graph.add_node("SafeSQLTool", node_safe_sql_tool)
    graph.add_node("RunbookRAGTool", node_runbook_rag_tool)
    graph.add_node("HallucinationGrader", node_hallucination_grader)
    graph.add_edge(START, "IntentRouter")
    graph.add_conditional_edges(
        "IntentRouter",
        lambda state: state["intent"],
        {
            "SQL_ANALYTICS": "SafeSQLTool",
            "RUNBOOK_RAG": "RunbookRAGTool",
        },
    )
    graph.add_edge("SafeSQLTool", "HallucinationGrader")
    graph.add_edge("RunbookRAGTool", "HallucinationGrader")
    graph.add_conditional_edges(
        "HallucinationGrader",
        _after_grading,
        {"IntentRouter": "IntentRouter", END: END},
    )
    return graph.compile()


_configure_telemetry()
agent_graph = _build_graph()
app = FastAPI(title="FDE SRE LangGraph Agent", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    tenant_id: str = Field(
        default="", max_length=63, pattern=r"^[a-zA-Z0-9_-]*$"
    )
    caller_role: str = "fde_admin"


def _run_agent(request: AskRequest) -> AgentState:
    result = agent_graph.invoke(
        {
            "query": request.query,
            "original_query": request.query,
            "caller_role": request.caller_role,
            "tenant_id": request.tenant_id,
            "rewrite_count": 0,
            "telemetry": {},
        }
    )
    return AgentState(
        query=result["original_query"],
        caller_role=request.caller_role,
        tenant_id=request.tenant_id,
        rewritten_query=(
            result["query"] if result["query"] != result["original_query"] else ""
        ),
        intent=result["intent"],
        retrieved_context=result["retrieved_context"],
        draft_answer=result["draft_answer"],
        grounded_score=result["grounded_score"],
        rewrite_count=result.get("rewrite_count", 0),
        telemetry=result["telemetry"],
    )


def run_fde_agent(
    query: str, role: str = "fde_admin", tenant_id: str = ""
) -> AgentState:
    return _run_agent(
        AskRequest(query=query, caller_role=role, tenant_id=tenant_id)
    )


def _annotate_request_span(
    span: Any, request: AskRequest, result: AgentState, ttft_ms: float
) -> None:
    prompt_tokens = len(re.findall(r"\w+|[^\w\s]", request.query))
    completion_tokens = len(re.findall(r"\w+|[^\w\s]", result.draft_answer))
    input_rate = float(os.getenv("INPUT_COST_PER_1M_TOKENS", "0"))
    output_rate = float(os.getenv("OUTPUT_COST_PER_1M_TOKENS", "0"))
    prompt_cost = prompt_tokens * input_rate / 1_000_000
    completion_cost = completion_tokens * output_rate / 1_000_000
    cost = prompt_cost + completion_cost
    span.set_attribute("tenant.id", request.tenant_id or "all-tenants")
    span.set_attribute("fde.ttft_ms", round(ttft_ms, 3))
    span.set_attribute("fde.token_count.prompt", prompt_tokens)
    span.set_attribute("fde.token_count.completion", completion_tokens)
    span.set_attribute("fde.token_cost_usd", cost)
    span.set_attribute("llm.token_count.prompt", prompt_tokens)
    span.set_attribute("llm.token_count.completion", completion_tokens)
    span.set_attribute("llm.token_count.total", prompt_tokens + completion_tokens)
    span.set_attribute("llm.cost.prompt", prompt_cost)
    span.set_attribute("llm.cost.completion", completion_cost)
    span.set_attribute("llm.cost.total", cost)
    span.set_attribute("fde.tool_latency_ms", result.telemetry["tool_latency_ms"])
    span.set_attribute("fde.faithfulness_score", result.grounded_score)
    span.set_attribute("fde.rewrite_count", result.rewrite_count)


def _response_body(result: AgentState) -> dict[str, Any]:
    return {
        "answer": result.draft_answer,
        "intent": result.intent,
        "tenant_id": result.tenant_id,
        "rewritten_query": result.rewritten_query,
        "grounded_score": result.grounded_score,
        "rewrite_count": result.rewrite_count,
        "telemetry": result.telemetry,
    }


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/v1/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    started = time.perf_counter()
    with _TRACER.start_as_current_span("fde.ask") as span:
        result = _run_agent(request)
        ttft_ms = (time.perf_counter() - started) * 1000
        _annotate_request_span(span, request, result, ttft_ms)
        return _response_body(result)


@app.post("/api/v1/ask/stream")
async def ask_stream(request: AskRequest) -> StreamingResponse:
    async def stream_answer():
        started = time.perf_counter()
        with _TRACER.start_as_current_span("fde.ask.stream") as span:
            result = await run_in_threadpool(_run_agent, request)
            ttft_ms = (time.perf_counter() - started) * 1000
            _annotate_request_span(span, request, result, ttft_ms)
            words = result.draft_answer.split()
            if not words:
                yield f"data: {json.dumps({'answer': '', 'done': True})}\n\n"
                return
            for index, word in enumerate(words):
                payload = {"token": word, "done": index == len(words) - 1}
                yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(stream_answer(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "agent_with_sre_evals:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError

import duckdb
import pytest
from fastapi.testclient import TestClient

import aegisops.api
from aegisops.api import (
    LLMUnavailableError,
    OpenAICompatibleChatClient,
    Role,
    Settings,
    create_app,
)
from aegisops.assistant import AskService, MarkdownRetriever
from aegisops.metrics import InstrumentedChatClient, Telemetry


@dataclass(frozen=True)
class FakeCompletion:
    content: str
    prompt_tokens: int = 12
    completion_tokens: int = 8


class FakeChatClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> FakeCompletion:
        self.prompts.append(prompt)
        if prompt.startswith("Write exactly one DuckDB SELECT"):
            return FakeCompletion(
                "SELECT service, status, observed_pct FROM sla_metrics "
                "WHERE service = 'payments-api' LIMIT 50"
            )
        return FakeCompletion(
            "SLA data shows the service breached its target. The retry-storm runbook "
            "identifies dependency slowdown and amplified retries as likely causes."
        )


def _create_metrics_database(path: Path) -> None:
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            CREATE TABLE sla_metrics (
                service VARCHAR,
                status VARCHAR,
                observed_pct DOUBLE
            )
            """
        )
        connection.execute(
            "INSERT INTO sla_metrics VALUES ('payments-api', 'breached', 98.7)"
        )


def _issue_token(client: TestClient, role: Role) -> str:
    response = client.post("/api/v1/demo/token", json={"role": role.value})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_end_to_end_synthesis_uses_sql_and_runbooks_and_filters_postmortems(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "sla.duckdb"
    _create_metrics_database(database_path)
    runbooks = tmp_path / "runbooks"
    runbooks.mkdir()
    (runbooks / "retry-storm.md").write_text(
        "Dependency slowdown caused retries to amplify the payments-api 5xx rate.",
        encoding="utf-8",
    )
    postmortems = tmp_path / "redacted-postmortems"
    postmortems.mkdir()
    (postmortems / "incident-42.md").write_text(
        "PRIVATE-SRE-ONLY: payments-api retried requests after a dependency slowdown. "
        "Contact <REDACTED> at <REDACTED>.",
        encoding="utf-8",
    )
    chat = FakeChatClient()
    service = AskService(
        chat=chat,
        retriever=MarkdownRetriever(runbooks, postmortems),
        database_path=database_path,
    )
    app = create_app(
        Settings(
            jwt_secret="test-secret-that-is-at-least-thirty-two-bytes",
            demo_token_issuer_enabled=True,
            llm_api_key="",
            llm_base_url="https://example.invalid/v1",
            llm_model="test-model",
            database_path=str(database_path),
            runbooks_directory=str(runbooks),
            redacted_postmortems_directory=str(postmortems),
            neon_database_url=None,
            embedding_model="test-embedding-model",
            embedding_dimensions=2,
            input_cost_per_million=2.0,
            output_cost_per_million=4.0,
        ),
        ask_service=service,
    )
    client = TestClient(app)
    question = "What caused the payments-api 5xx rate after dependency retries?"

    sre_token = _issue_token(client, Role.SRE_LEAD)
    sre_response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {sre_token}"},
        json={"question": question},
    )
    assert sre_response.status_code == 200
    sre_result = sre_response.json()
    assert sre_result["sql_results"] == [
        {"service": "payments-api", "status": "breached", "observed_pct": 98.7}
    ]
    assert sre_result["sql_query"].startswith("SELECT")
    assert "runbook:retry-storm.md" in sre_result["sources"]
    assert "postmortem:incident-42.md" in sre_result["sources"]
    assert "PRIVATE-SRE-ONLY" in chat.prompts[-1]
    assert "breached" in chat.prompts[-1]

    support_token = _issue_token(client, Role.TIER1_SUPPORT)
    support_response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {support_token}"},
        json={"question": question},
    )
    assert support_response.status_code == 200
    assert "runbook:retry-storm.md" in support_response.json()["sources"]
    assert not any(
        source.startswith("postmortem:")
        for source in support_response.json()["sources"]
    )
    assert "PRIVATE-SRE-ONLY" not in chat.prompts[-1]

    auditor_token = _issue_token(client, Role.EXTERNAL_AUDITOR)
    auditor_response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {auditor_token}"},
        json={"question": question},
    )
    assert auditor_response.status_code == 200
    assert not any(
        source.startswith("postmortem:")
        for source in auditor_response.json()["sources"]
    )
    assert "PRIVATE-SRE-ONLY" not in chat.prompts[-1]

    control_plane = client.get(
        "/api/v1/control-plane",
        headers={"Authorization": f"Bearer {support_token}"},
    ).json()
    assert control_plane["api_p95_latency_seconds"] is not None
    assert control_plane["cost_pricing_configured"] is True
    assert control_plane["circuit_breaker_status"] == "closed"
    assert control_plane["pii_entities_redacted_total"] == 2
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "aegisops_llm_tokens_total" in metrics_response.text
    assert "aegisops_pii_entities_redacted_indexed 2.0" in metrics_response.text


def test_api_requires_token_and_demo_issuer_is_disabled_by_default(tmp_path: Path) -> None:
    database_path = tmp_path / "sla.duckdb"
    _create_metrics_database(database_path)
    settings = Settings(
        jwt_secret="test-secret-that-is-at-least-thirty-two-bytes",
        demo_token_issuer_enabled=False,
        llm_api_key="",
        llm_base_url="https://example.invalid/v1",
        llm_model="test-model",
        database_path=str(database_path),
        runbooks_directory=str(tmp_path / "runbooks"),
        redacted_postmortems_directory=None,
        neon_database_url=None,
        embedding_model="test-embedding-model",
        embedding_dimensions=2,
        input_cost_per_million=0,
        output_cost_per_million=0,
    )
    client = TestClient(create_app(settings))
    assert client.post("/api/v1/demo/token", json={"role": "sre_lead"}).status_code == 404
    assert client.post("/api/v1/ask", json={"question": "incident root cause"}).status_code == 401


def test_sql_agent_rejects_queries_outside_sla_table(tmp_path: Path) -> None:
    database_path = tmp_path / "sla.duckdb"
    _create_metrics_database(database_path)
    runbooks = tmp_path / "runbooks"
    runbooks.mkdir()

    class UnsafePlanner:
        def complete(self, prompt: str) -> FakeCompletion:
            return FakeCompletion("SELECT * FROM read_csv_auto('/etc/passwd')")

    service = AskService(
        chat=UnsafePlanner(),
        retriever=MarkdownRetriever(runbooks),
        database_path=database_path,
    )
    try:
        service.ask("show metrics", "sre_lead")
    except ValueError as error:
        assert "sla_metrics" in str(error)
    else:
        raise AssertionError("Unsafe SQL was not rejected")


def test_instrumented_chat_client_tracks_usage_and_cost() -> None:
    telemetry = Telemetry()
    client = InstrumentedChatClient(
        FakeChatClient(),
        telemetry,
        input_cost_per_million=2,
        output_cost_per_million=4,
    )
    client.complete("prompt")
    snapshot = telemetry.snapshot()
    assert snapshot["llm_tokens_total"] == 20
    assert snapshot["llm_cost_usd_total"] == (12 * 2 + 8 * 4) / 1_000_000


def test_chat_client_includes_network_failure_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_request(*args: object, **kwargs: object) -> None:
        raise URLError("Name or service not known")

    monkeypatch.setattr(aegisops.api, "urlopen", fail_request)
    client = OpenAICompatibleChatClient(
        "test-key", "https://example.invalid/v1", "test-model"
    )

    with pytest.raises(LLMUnavailableError, match="Name or service not known"):
        client.complete("test prompt")


def test_circuit_breaker_opens_and_pii_redaction_is_counted() -> None:
    class FailingChatClient:
        def complete(self, prompt: str) -> FakeCompletion:
            raise RuntimeError("LLM unavailable")

    telemetry = Telemetry()
    client = InstrumentedChatClient(FailingChatClient(), telemetry, failure_threshold=3)
    for _ in range(3):
        try:
            client.complete("prompt")
        except RuntimeError:
            pass
        else:
            raise AssertionError("LLM errors must propagate")
    assert telemetry.snapshot()["circuit_breaker_status"] == "open"

    telemetry.record_pii_redactions(2)
    assert telemetry.snapshot()["pii_entities_redacted_total"] >= 2
from day18_19_langraph_otel_llm.agent_with_sre_evals import AskRequest, _run_agent


def test_sql_intent_returns_tenant_scoped_read_only_metrics():
    result = _run_agent(
        AskRequest(
            query="How many SLA breaches did this tenant have?",
            tenant_id="acme_health",
        )
    )

    assert result.intent == "SQL_ANALYTICS"
    assert "tenant_id=acme_health" in result.draft_answer
    assert "value=3" in result.draft_answer
    assert result.grounded_score >= 0.5
    assert result.rewrite_count == 0


def test_sql_query_without_tenant_returns_cross_tenant_metrics():
    result = _run_agent(AskRequest(query="Which tenant had SLA breaches?"))

    assert "tenant_id=acme_health" in result.draft_answer
    assert "tenant_id=northstar" in result.draft_answer


def test_runbook_intent_retrieves_matching_evidence():
    result = _run_agent(
        AskRequest(query="What should I check for ERR_SSL_09?")
    )

    assert result.intent == "RUNBOOK_RAG"
    assert "ERR_SSL_09" in result.retrieved_context
    assert result.grounded_score >= 0.5


def test_ungrounded_answer_is_rewritten_only_once_then_abstains():
    result = _run_agent(AskRequest(query="ERR_UNDOCUMENTED_404"))

    assert result.rewrite_count == 1
    assert result.grounded_score == 0.0
    assert result.query == "ERR_UNDOCUMENTED_404"
    assert "Runbook evidence" in result.rewritten_query
    assert result.draft_answer.startswith("I could not ground an answer")

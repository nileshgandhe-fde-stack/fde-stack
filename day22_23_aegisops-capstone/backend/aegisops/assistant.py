"""Role-aware hybrid retrieval and SQL synthesis workflow."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict

import duckdb
import sqlglot
from langgraph.graph import END, START, StateGraph
from sqlglot import exp


class ChatCompletion(Protocol):
    content: str
    prompt_tokens: int
    completion_tokens: int


class ChatClient(Protocol):
    def complete(self, prompt: str) -> ChatCompletion: ...


class EmbeddingClient(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class RetrievedDocument:
    source: str
    content: str
    access: str


class AskState(TypedDict):
    question: str
    role: str
    sql: NotRequired[str]
    sql_results: NotRequired[list[dict[str, object]]]
    documents: NotRequired[list[RetrievedDocument]]
    answer: NotRequired[str]


class UnsafeQueryError(ValueError):
    """Raised when a generated SQL query exceeds the allowed read-only scope."""


class PostgresRetrievalError(RuntimeError):
    """Raised when semantic post-mortem retrieval or index telemetry fails."""


def validate_metrics_query(query: str, max_rows: int = 50) -> str:
    """Allow one SELECT against the SLA table, and cap returned rows."""
    statements = sqlglot.parse(query, read="duckdb")
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise UnsafeQueryError("Only one SELECT statement is allowed")

    statement = statements[0]
    tables = {table.name.lower() for table in statement.find_all(exp.Table)}
    if tables != {"sla_metrics"}:
        raise UnsafeQueryError("Queries may only read the sla_metrics table")
    functions = {
        function.sql_name().upper()
        for function in statement.find_all(exp.Func)
        if function.sql_name()
    }
    allowed_functions = {"AVG", "COUNT", "MAX", "MIN", "ROUND", "SUM"}
    if functions - allowed_functions:
        raise UnsafeQueryError("The query uses a function that is not allowed")

    limit = statement.args.get("limit")
    if limit is None:
        statement = statement.limit(max_rows)
    else:
        try:
            requested_limit = int(limit.expression.this)
        except (AttributeError, TypeError, ValueError):
            raise UnsafeQueryError("The query limit must be a numeric literal") from None
        if requested_limit < 1:
            raise UnsafeQueryError("The query limit must be positive")
        if requested_limit > max_rows:
            statement = statement.limit(max_rows)
    return statement.sql(dialect="duckdb")


def _terms(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    normalized = set()
    for word in words:
        normalized.add(word)
        if len(word) > 4 and word.endswith("ies"):
            normalized.add(f"{word[:-3]}y")
        elif len(word) > 4 and word.endswith(("ing", "ed", "es")):
            normalized.add(word[:-3] if word.endswith("ing") else word[:-2])
    normalized = {word for word in normalized if len(word) > 2}
    return normalized


class MarkdownRetriever:
    """Lexically retrieve runbooks and SRE-only, pre-redacted post-mortems."""

    def __init__(
        self,
        runbooks_directory: str | Path,
        redacted_postmortems_directory: str | Path | None = None,
        *,
        vector_retriever: PostgresVectorRetriever | None = None,
        top_k: int = 3,
    ) -> None:
        self._runbooks_directory = Path(runbooks_directory)
        self._postmortems_directory = (
            Path(redacted_postmortems_directory) if redacted_postmortems_directory else None
        )
        self._vector_retriever = vector_retriever
        self._top_k = top_k

    def retrieve(self, question: str, role: str) -> list[RetrievedDocument]:
        semantic_documents = (
            self._vector_retriever.retrieve(question, role)
            if self._vector_retriever is not None
            else []
        )
        candidates: list[RetrievedDocument] = []
        candidates.extend(self._load(self._runbooks_directory, "runbook", "all"))
        if role == "sre_lead" and self._postmortems_directory is not None:
            candidates.extend(self._load(self._postmortems_directory, "postmortem", "sre_lead"))

        query_terms = _terms(question)
        lexical_documents = sorted(
            candidates,
            key=lambda document: (
                len(query_terms & _terms(document.content)),
                document.source,
            ),
            reverse=True,
        )
        lexical_documents = [
            document
            for document in lexical_documents[: self._top_k]
            if query_terms & _terms(document.content)
        ]
        combined: list[RetrievedDocument] = []
        seen_sources: set[str] = set()
        for document in [*semantic_documents, *lexical_documents]:
            if document.source not in seen_sources:
                combined.append(document)
                seen_sources.add(document.source)
            if len(combined) == self._top_k:
                break
        return combined

    def redacted_entity_count(self) -> int | None:
        local_count = 0
        if self._postmortems_directory is not None and self._postmortems_directory.is_dir():
            local_count = sum(
                path.read_text(encoding="utf-8").count("<REDACTED>")
                for path in self._postmortems_directory.glob("*.md")
                if path.is_file()
            )
        if self._vector_retriever is not None:
            return local_count + self._vector_retriever.redacted_entity_count()
        if self._postmortems_directory is not None:
            return local_count
        return None

    @staticmethod
    def _load(directory: Path, source: str, access: str) -> list[RetrievedDocument]:
        if not directory.is_dir():
            return []
        return [
            RetrievedDocument(
                source=f"{source}:{path.name}",
                content=path.read_text(encoding="utf-8"),
                access=access,
            )
            for path in sorted(directory.glob("*.md"))
            if path.is_file()
        ]


class PostgresVectorRetriever:
    """Search the redacted post-mortem pgvector index for SRE users only."""

    def __init__(
        self,
        database_url: str,
        embedder: EmbeddingClient,
        *,
        top_k: int = 3,
    ) -> None:
        self._database_url = database_url
        self._embedder = embedder
        self._top_k = top_k

    def retrieve(self, question: str, role: str) -> list[RetrievedDocument]:
        if role != "sre_lead":
            return []
        try:
            vectors = self._embedder.embed([question])
        except RuntimeError as error:
            raise PostgresRetrievalError("Could not create a post-mortem search embedding") from error
        if len(vectors) != 1:
            raise PostgresRetrievalError(
                "The embedding service returned an unexpected number of vectors"
            )

        import psycopg
        from pgvector import Vector
        from pgvector.psycopg import register_vector

        try:
            with psycopg.connect(self._database_url, connect_timeout=5) as connection:
                register_vector(connection)
                connection.execute("SET statement_timeout = '5000ms'")
                rows = connection.execute(
                    """
                    SELECT source_path, content
                    FROM postmortems
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (Vector(vectors[0]), self._top_k),
                ).fetchall()
        except psycopg.Error as error:
            raise PostgresRetrievalError("The post-mortem index is unavailable") from error
        return [
            RetrievedDocument(
                source=f"postmortem:{source_path}",
                content=content,
                access="sre_lead",
            )
            for source_path, content in rows
        ]

    def redacted_entity_count(self) -> int:
        import psycopg

        try:
            with psycopg.connect(self._database_url, connect_timeout=5) as connection:
                connection.execute("SET statement_timeout = '5000ms'")
                row = connection.execute(
                    """
                    SELECT COALESCE(
                        SUM(
                            (length(content) - length(replace(content, '<REDACTED>', '')))
                            / length('<REDACTED>')
                        ),
                        0
                    )
                    FROM postmortems
                    """
                ).fetchone()
        except psycopg.Error as error:
            raise PostgresRetrievalError("The post-mortem index is unavailable") from error
        return int(row[0])


class AskService:
    def __init__(
        self,
        *,
        chat: ChatClient,
        retriever: MarkdownRetriever,
        database_path: str | Path,
    ) -> None:
        self._chat = chat
        self._retriever = retriever
        self._database_path = str(database_path)
        graph = StateGraph(AskState)
        graph.add_node("query_metrics", self._query_metrics)
        graph.add_node("retrieve_documents", self._retrieve_documents)
        graph.add_node("synthesize", self._synthesize)
        graph.add_edge(START, "query_metrics")
        graph.add_edge("query_metrics", "retrieve_documents")
        graph.add_edge("retrieve_documents", "synthesize")
        graph.add_edge("synthesize", END)
        self._graph = graph.compile()

    def ask(self, question: str, role: str) -> dict[str, object]:
        result = self._graph.invoke({"question": question, "role": role})
        return {
            "answer": result["answer"],
            "sql_query": result["sql"],
            "sql_results": result["sql_results"],
            "sources": [document.source for document in result["documents"]],
        }

    def redacted_entity_count(self) -> int | None:
        return self._retriever.redacted_entity_count()

    def _query_metrics(self, state: AskState) -> dict[str, object]:
        prompt = (
            "Write exactly one DuckDB SELECT query for incident/SLA metrics. "
            "Use only the sla_metrics table and these columns: sla_id, measured_at, "
            "tenant_id, service, region, monthly_target_pct, observed_pct, request_count, "
            "error_count, status, source_note. Use no other table or columns and only "
            "these functions if needed: AVG, COUNT, MAX, MIN, ROUND, SUM. Do not use "
            "any other statement. Add LIMIT 50. Return SQL only.\n"
            f"Question: {state['question']}"
        )
        generated_sql = self._chat.complete(prompt).content
        try:
            sql = validate_metrics_query(generated_sql)
        except UnsafeQueryError as error:
            repair_prompt = (
                f"{prompt}\nThe previous query was rejected: {error}. "
                "Generate a corrected query that follows every restriction. "
                "Return SQL only."
            )
            sql = validate_metrics_query(self._chat.complete(repair_prompt).content)
        with duckdb.connect(self._database_path, read_only=True) as connection:
            cursor = connection.execute(sql)
            columns = [column[0] for column in cursor.description or ()]
            rows = [
                dict(zip(columns, row, strict=True))
                for row in cursor.fetchmany(50)
            ]
        return {"sql": sql, "sql_results": rows}

    def _retrieve_documents(self, state: AskState) -> dict[str, object]:
        documents = self._retriever.retrieve(state["question"], state["role"])
        return {"documents": documents}

    def _synthesize(self, state: AskState) -> dict[str, str]:
        evidence = [
            {
                "source": document.source,
                "access": document.access,
                "content": document.content,
            }
            for document in state["documents"]
        ]
        prompt = (
            "Synthesize an incident root-cause answer using only the supplied SQL results "
            "and retrieved Markdown. Clearly separate observed metrics from likely causes, "
            "cite source names, and state when evidence is insufficient. Do not invent "
            "facts or expose information absent from these sources.\n"
            f"Question: {state['question']}\n"
            f"SQL: {state['sql']}\n"
            f"SQL results: {json.dumps(state['sql_results'], default=str)}\n"
            f"Retrieved documents: {json.dumps(evidence)}"
        )
        return {"answer": self._chat.complete(prompt).content}
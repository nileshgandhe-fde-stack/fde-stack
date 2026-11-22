"""Ingest redacted post-mortems into Neon and SLA metrics into DuckDB."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from aegisops.metrics import record_pii_entities_redacted


@dataclass(frozen=True)
class Document:
    document_id: str
    source_path: str
    content: str


class Redactor(Protocol):
    def redact(self, text: str) -> str: ...


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    def upsert_documents(
        self, documents: Sequence[Document], embeddings: Sequence[Sequence[float]]
    ) -> None: ...


class PresidioRedactor:
    """Redact recognized entities with Presidio's replacement operator."""

    def __init__(
        self,
        analyzer: object | None = None,
        anonymizer: object | None = None,
        language: str = "en",
    ) -> None:
        if analyzer is None:
            from presidio_analyzer import AnalyzerEngine

            analyzer = AnalyzerEngine()
        if anonymizer is None:
            from presidio_anonymizer import AnonymizerEngine

            anonymizer = AnonymizerEngine()

        self._analyzer = analyzer
        self._anonymizer = anonymizer
        self._language = language

    def redact(self, text: str) -> str:
        from presidio_anonymizer import OperatorConfig

        results = self._analyzer.analyze(text=text, language=self._language)
        redacted = self._anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})},
        )
        record_pii_entities_redacted(len(results))
        return redacted.text


class OpenAICompatibleEmbedder:
    """Call an OpenAI-compatible embeddings endpoint using the standard library."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("An embeddings API key is required")
        if dimensions < 1:
            raise ValueError("Embedding dimensions must be positive")
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._url = f"{base_url.rstrip('/')}/embeddings"
        self._timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        request = Request(
            self._url,
            data=json.dumps(
                {"input": list(texts), "model": self._model, "dimensions": self._dimensions}
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            raise RuntimeError(f"Embedding service returned HTTP {error.code}") from error
        except URLError as error:
            raise RuntimeError("Could not reach the embedding service") from error

        data = payload["data"]
        if len(data) != len(texts):
            raise ValueError("Embedding service returned an unexpected number of vectors")
        ordered = sorted(data, key=lambda item: item["index"])
        embeddings = [item["embedding"] for item in ordered]
        if any(len(vector) != self._dimensions for vector in embeddings):
            raise ValueError("Embedding service returned a vector with unexpected dimensions")
        return embeddings


class NeonPgVectorStore:
    """Persist sanitized document text and embeddings in a Neon pgvector table."""

    def __init__(self, dsn: str, dimensions: int = 1536) -> None:
        if dimensions < 1:
            raise ValueError("Embedding dimensions must be positive")
        import psycopg
        from pgvector.psycopg import register_vector

        self._dimensions = dimensions
        self._connection = psycopg.connect(dsn)
        try:
            register_vector(self._connection)
            with self._connection.transaction():
                self._connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
                self._connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS postmortems (
                        document_id TEXT PRIMARY KEY,
                        source_path TEXT NOT NULL,
                        content TEXT NOT NULL,
                        embedding vector({dimensions}) NOT NULL,
                        indexed_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
        except Exception:
            self._connection.close()
            raise

    def upsert_documents(
        self, documents: Sequence[Document], embeddings: Sequence[Sequence[float]]
    ) -> None:
        if len(documents) != len(embeddings):
            raise ValueError("Each document must have exactly one embedding")
        from pgvector import Vector

        with self._connection.transaction():
            for document, embedding in zip(documents, embeddings, strict=True):
                if len(embedding) != self._dimensions:
                    raise ValueError(
                        f"Expected {self._dimensions}-dimension embeddings, "
                        f"received {len(embedding)}"
                    )
                self._connection.execute(
                    """
                    INSERT INTO postmortems (document_id, source_path, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (document_id) DO UPDATE SET
                        source_path = EXCLUDED.source_path,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        indexed_at = now()
                    """,
                    (
                        document.document_id,
                        document.source_path,
                        document.content,
                        Vector(embedding),
                    ),
                )

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> NeonPgVectorStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class DuckDBSlaStore:
    """Load generated SLA CSV rows into a typed, idempotent DuckDB table."""

    def __init__(self, database_path: str | Path) -> None:
        import duckdb

        self._connection = duckdb.connect(str(database_path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sla_metrics (
                sla_id VARCHAR PRIMARY KEY,
                measured_at TIMESTAMPTZ NOT NULL,
                tenant_id VARCHAR NOT NULL,
                service VARCHAR NOT NULL,
                region VARCHAR NOT NULL,
                monthly_target_pct DOUBLE NOT NULL,
                observed_pct DOUBLE NOT NULL,
                request_count BIGINT NOT NULL,
                error_count BIGINT NOT NULL,
                status VARCHAR NOT NULL,
                source_note VARCHAR NOT NULL
            )
            """
        )

    def load_csv(self, csv_path: str | Path) -> int:
        path = str(Path(csv_path).resolve())
        count = self._connection.execute(
            "SELECT count(*) FROM read_csv_auto(?, header = true)", [path]
        ).fetchone()[0]
        self._connection.execute(
            """
            INSERT INTO sla_metrics
            SELECT
                sla_id, measured_at, tenant_id, service, region,
                monthly_target_pct, observed_pct, request_count, error_count,
                status, source_note
            FROM read_csv_auto(?, header = true)
            ON CONFLICT (sla_id) DO UPDATE SET
                measured_at = EXCLUDED.measured_at,
                tenant_id = EXCLUDED.tenant_id,
                service = EXCLUDED.service,
                region = EXCLUDED.region,
                monthly_target_pct = EXCLUDED.monthly_target_pct,
                observed_pct = EXCLUDED.observed_pct,
                request_count = EXCLUDED.request_count,
                error_count = EXCLUDED.error_count,
                status = EXCLUDED.status,
                source_note = EXCLUDED.source_note
            """,
            [path],
        )
        return count

    def count(self) -> int:
        return self._connection.execute("SELECT count(*) FROM sla_metrics").fetchone()[0]

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> DuckDBSlaStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def ingest_postmortems(
    docs_directory: str | Path,
    redactor: Redactor,
    embedder: Embedder,
    vector_store: VectorStore,
) -> int:
    """Redact each Markdown document before embedding or persistence."""
    paths = sorted(Path(docs_directory).glob("*.md"))
    documents: list[Document] = []
    for path in paths:
        sanitized = redactor.redact(path.read_text(encoding="utf-8"))
        document_id = hashlib.sha256(path.name.encode("utf-8")).hexdigest()
        documents.append(Document(document_id, path.name, sanitized))
    embeddings = embedder.embed([document.content for document in documents])
    if len(embeddings) != len(documents):
        raise ValueError("Embedder returned an unexpected number of vectors")
    vector_store.upsert_documents(documents, embeddings)
    return len(documents)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=Path("data_seed/generated/postmortems"))
    parser.add_argument("--sla-csv", type=Path, default=Path("data_seed/generated/tenant_sla.csv"))
    parser.add_argument("--duckdb-path", type=Path, default=Path("data_seed/generated/aegisops.duckdb"))
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    database_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY to use the configured embeddings service")
    if not database_url:
        raise ValueError("Set NEON_DATABASE_URL (or DATABASE_URL) for Neon pgvector")

    dimensions = int(os.environ.get("OPENAI_EMBEDDING_DIMENSIONS", "1536"))
    embedder = OpenAICompatibleEmbedder(
        api_key=api_key,
        model=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        dimensions=dimensions,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    with NeonPgVectorStore(database_url, dimensions) as vector_store:
        document_count = ingest_postmortems(
            args.docs_dir, PresidioRedactor(), embedder, vector_store
        )
    with DuckDBSlaStore(args.duckdb_path) as sla_store:
        sla_count = sla_store.load_csv(args.sla_csv)
    print(f"Indexed {document_count} redacted post-mortems; loaded {sla_count} SLA rows.")


if __name__ == "__main__":
    main()

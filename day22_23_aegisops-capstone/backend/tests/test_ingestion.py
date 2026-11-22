from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Sequence

if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository_root))
    sys.path.insert(0, str(repository_root / "backend"))

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine

from aegisops.ingestion import (
    Document,
    DuckDBSlaStore,
    PresidioRedactor,
    ingest_postmortems,
)
from data_seed.seed_enterprise_data import generate


class SyntheticPiiAnalyzer:
    """Provide deterministic Presidio results without loading an NLP model."""

    def analyze(self, text: str, language: str) -> list[RecognizerResult]:
        assert language == "en"
        return [
            RecognizerResult(
                start=match.start(),
                end=match.end(),
                entity_type=entity_type,
                score=1.0,
            )
            for entity_type, pattern in (
                ("EMAIL_ADDRESS", r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
                ("PHONE_NUMBER", r"\+1-202-555-\d{4}"),
            )
            for match in re.finditer(pattern, text)
        ]


class RecordingEmbedder:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.texts.extend(texts)
        return [[0.0, 1.0] for _ in texts]


class RecordingVectorStore:
    def __init__(self) -> None:
        self.documents: list[Document] = []
        self.embeddings: list[Sequence[float]] = []

    def upsert_documents(
        self, documents: Sequence[Document], embeddings: Sequence[Sequence[float]]
    ) -> None:
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)


def test_generated_dataset_counts_and_duckdb_ingestion(tmp_path: Path) -> None:
    alerts_path, docs_dir, sla_path = generate(
        tmp_path / "seed",
        seed=9,
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with alerts_path.open(encoding="utf-8") as file:
        alerts = [json.loads(line) for line in file]
    assert len(alerts) == 1_000
    assert {alert["source"] for alert in alerts} == {"pagerduty", "prometheus"}
    assert len(list(docs_dir.glob("*.md"))) == 50
    with DuckDBSlaStore(tmp_path / "sla.duckdb") as store:
        assert store.load_csv(sla_path) == 10_000
        assert store.count() == 10_000
        assert store.load_csv(sla_path) == 10_000
        assert store.count() == 10_000


def test_postmortems_are_redacted_before_embedding_and_indexing(tmp_path: Path) -> None:
    docs_dir = tmp_path / "postmortems"
    docs_dir.mkdir()
    (docs_dir / "incident.md").write_text(
        "Contact Alex at alex.morgan@example.com or +1-202-555-0101.", encoding="utf-8"
    )
    redactor = PresidioRedactor(
        analyzer=SyntheticPiiAnalyzer(),
        anonymizer=AnonymizerEngine(),
    )
    embedder = RecordingEmbedder()
    vector_store = RecordingVectorStore()

    assert ingest_postmortems(docs_dir, redactor, embedder, vector_store) == 1
    assert len(vector_store.documents) == 1
    assert "alex.morgan@example.com" not in embedder.texts[0]
    assert "+1-202-555-0101" not in embedder.texts[0]
    assert "alex.morgan@example.com" not in vector_store.documents[0].content
    assert "+1-202-555-0101" not in vector_store.documents[0].content
    assert "<REDACTED>" in vector_store.documents[0].content
    assert embedder.texts[0] == vector_store.documents[0].content


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))

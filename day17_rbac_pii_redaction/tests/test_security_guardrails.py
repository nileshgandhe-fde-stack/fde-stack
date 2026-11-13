import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import HTTPException

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from day4_oidc_and_rbac.rbac_auth_service import (
    get_verified_roles,
    issue_test_jwt,
    verify_access_token,
)
from day15_16_hybrid_search_rag import hybrid_rag_rrf as rag
from day17_rbac_pii_redaction.pii_redaction_guardrail import scrub_enterprise_pii
from day17_rbac_pii_redaction.rag_api import AskRequest, ask_documents


def test_presidio_redacts_direct_identifiers() -> None:
    raw_text = (
        "Patient John Doe, MRN: MRN-123456, card 4111-1111-1111-1111, "
        "john.doe@example.org, 415-890-2211"
    )

    scrubbed, counts = scrub_enterprise_pii(raw_text)

    assert all(value not in scrubbed for value in (
        "John Doe",
        "MRN-123456",
        "4111-1111-1111-1111",
        "john.doe@example.org",
        "415-890-2211",
    ))
    assert all(token in scrubbed for token in {
        "<PERSON>",
        "<PATIENT_ID>",
        "<CREDIT_CARD>",
        "<EMAIL_ADDRESS>",
        "<PHONE_NUMBER>",
    })
    assert {"PERSON", "PATIENT_ID", "CREDIT_CARD", "EMAIL_ADDRESS", "PHONE_NUMBER"} <= (
        counts.keys()
    )
    print("PASS: Presidio redacts names, patient IDs, cards, emails, and phones")


def test_viewer_jwt_cannot_retrieve_or_infer_executive_document(monkeypatch) -> None:
    token = issue_test_jwt(username="viewer", roles=["viewer"])["access_token"]
    claims = verify_access_token(token)
    verified_role = get_verified_roles(claims)[0]
    executive_secret = "Acquisition target is Northstar with a $40M offer."
    documents = [
        {
            "doc_id": "executive-only",
            "service_name": "strategy",
            "allowed_roles": ["executive_only"],
            "heading_path": "M&A",
            "content": executive_secret,
            "score": 1.0,
        },
        {
            "doc_id": "viewer-doc",
            "service_name": "support",
            "allowed_roles": ["viewer"],
            "heading_path": "Support",
            "content": "Public service status: operational.",
            "score": 0.5,
        },
    ]

    class FakeCursor:
        description = [
            SimpleNamespace(name=name)
            for name in (
                "doc_id",
                "service_name",
                "allowed_roles",
                "heading_path",
                "content",
                "score",
            )
        ]

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def execute(self, query, params):
            assert query.count("= ANY(c.allowed_roles)") == 2
            self.rows = [
                tuple(document[key] for key in (
                    "doc_id",
                    "service_name",
                    "allowed_roles",
                    "heading_path",
                    "content",
                    "score",
                ))
                for document in documents
                if params["role"] in document["allowed_roles"]
            ]

        def fetchall(self):
            return self.rows

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def cursor(self):
            return FakeCursor()

    class FakeEmbedding:
        def encode(self, *_args, **_kwargs):
            return SimpleNamespace(tolist=lambda: [0.0] * 384)

    captured_messages = []

    class FakeGroq:
        def __init__(self):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured_messages.extend(kwargs["messages"])
                    return SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
                    )

    monkeypatch.setattr(rag, "connect_database", lambda: FakeConnection())
    monkeypatch.setattr(rag, "get_embedding_model", lambda: FakeEmbedding())
    fake_groq_module = ModuleType("groq")
    fake_groq_module.Groq = FakeGroq
    monkeypatch.setitem(sys.modules, "groq", fake_groq_module)

    with pytest.raises(HTTPException) as error:
        ask_documents(
            AskRequest(query="What is in the executive strategy?", role="executive_only"),
            claims,
        )
    assert error.value.status_code == 403

    retrieved = rag.retrieve_chunks("What is in the executive strategy?", verified_role)
    response = ask_documents(
        AskRequest(query="What is in the executive strategy?"),
        claims,
    )

    assert [chunk["doc_id"] for chunk in retrieved] == ["viewer-doc"]
    assert response == {"answer": "ok"}
    assert executive_secret not in str(captured_messages)
    assert "Public service status" in str(captured_messages)
    print("PASS: viewer JWT cannot retrieve or infer executive-only content")


def test_schema_and_retrieval_use_role_array() -> None:
    source = (
        Path(__file__).parents[2]
        / "day15_16_hybrid_search_rag"
        / "hybrid_rag_rrf.py"
    ).read_text(encoding="utf-8")

    assert "allowed_roles text[] NOT NULL" in source
    assert source.count("WHERE %(role)s = ANY(c.allowed_roles)") == 2
    print("PASS: schema and keyword/vector queries enforce allowed_roles")

# Day 17: Role-Filtered Retrieval and PII Redaction

## Overview

This folder adds PII redaction and role-aware document retrieval to the hybrid
search exercise in [`day15_16_hybrid_search_rag`](../day15_16_hybrid_search_rag).
It includes a standalone Presidio redaction helper and a JWT-protected FastAPI
endpoint for asking questions about indexed documents.

## Business purpose

Operational documents can contain personal or patient identifiers and may
have different access policies. This module demonstrates two protections:
redact supported sensitive entities before sending prompts to the LLM, and
filter retrieval candidates by a role taken from a verified JWT.

## Key components

- `pii_redaction_guardrail.py` uses Presidio Analyzer and Anonymizer to replace
  person names, email addresses, phone numbers, credit-card numbers, and
  recognized patient IDs with typed tokens such as `<PERSON>`.
- `rag_api.py` validates a Day 4 JWT, checks any requested role against the
  verified token roles, and calls the Day 15 answer function.
- `tests/test_security_guardrails.py` covers redaction and role/security
  guardrails.
- Day 15's `document_chunks.allowed_roles` column filters keyword and vector
  candidates before ranking.

The CLI role option in Day 15 is for local demonstrations; applications must
pass roles from verified token claims, never from untrusted client input.

## API and data flow

`POST /api/v1/documents/ask` accepts a bearer token and a JSON body containing
`query`. An optional `role` can select one of the roles in the token; if the
token has multiple roles and no role is selected, the endpoint returns `400`.
An absent/invalid bearer token is rejected by the Day 4 dependency, and a role
not present in verified claims is rejected with `403`.

The answer function redacts the question before retrieval and redacts retrieved
context before constructing the Groq request. Retrieval uses PostgreSQL with
pgvector and the Day 15 schema. Initialize or migrate that schema with Day 15's
`init` command before ingesting documents.

## Setup and run

From the repository root, install the dependencies:

```bash
python -m pip install -r day17_rbac_pii_redaction/requirements.txt
python -m pip install -r day15_16_hybrid_search_rag/requirements.txt
python -m spacy download en_core_web_lg
```

Set `DATABASE_URL` to the PostgreSQL/pgvector database and `GROQ_API_KEY` for
answer generation. The Presidio English PERSON recognizer uses the
`en_core_web_lg` spaCy model.

Start the API:

```bash
uvicorn day17_rbac_pii_redaction.rag_api:app
```

Run the focused tests:

```bash
python -m pytest day17_rbac_pii_redaction/tests -q
```

Use the Day 4 demo JWT service only for local testing. Its demo issuer and
signing configuration are not production authentication.

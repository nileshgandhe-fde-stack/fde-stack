# Day 17: RBAC retrieval and PII redaction

The hybrid search stores each chunk's access policy in `document_chunks.allowed_roles`
(`text[]`). Both keyword and vector candidate queries require the role parameter to
match an element of that array before a chunk can be ranked or returned.

An application must take the role from Day 4's `get_current_user_claims` verified
JWT payload (via `get_verified_roles`) and pass that role to `retrieve_chunks` or
`answer_query`. Do not use client-supplied role values as authorization. The
standalone `--role` CLI option is for local demonstrations only.

The authenticated API in `rag_api.py` exposes `POST /api/v1/documents/ask`. It
validates the bearer JWT through Day 4 and accepts an optional role only when that
role is present in the verified claims. Install both Day 17 and Day 15 requirements
to run the API and RAG pipeline.

Install the security middleware and test dependencies from the repository root:

```bash
python -m pip install -r day17_rbac_pii_redaction/requirements.txt
python -m pip install -r day15_16_hybrid_search_rag/requirements.txt
python -m spacy download en_core_web_lg
python -m pytest day17_rbac_pii_redaction/tests
```

On a CPU-only machine, install the CPU PyTorch build first to avoid installing
CUDA packages:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r day15_16_hybrid_search_rag/requirements.txt
```

Run the API from the repository root with
`uvicorn day17_rbac_pii_redaction.rag_api:app` after setting `DATABASE_URL` and
`GROQ_API_KEY`.

The middleware uses Presidio Analyzer for `PERSON`, email, phone, credit-card, and
patient/MRN detection, then Presidio Anonymizer replaces matches with typed tokens
such as `<PERSON>` and `<PATIENT_ID>`. `answer_query` scrubs both the query and
retrieved context before constructing the Groq request. Presidio's English PERSON
recognizer requires the `en_core_web_lg` spaCy model.

Re-run `python -m day15_16_hybrid_search_rag.hybrid_rag_rrf init` after updating the
Day 15 schema. Existing `runbook_chunks` rows are migrated to `document_chunks`
with their previous role converted to a one-element `allowed_roles` array.


Use pytest rather than running the file directly—python test_security_guardrails.py does not execute pytest test functions. From the repository root, run:
`python -m pytest day17_rbac_pii_redaction/tests/test_security_guardrails.py -q`



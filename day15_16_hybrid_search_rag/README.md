# Day 15–16: Hybrid Search and Runbook RAG

## Overview

This folder implements a command-line pipeline for chunking Markdown
operational documents, embedding the chunks, storing them in PostgreSQL with
pgvector, and answering questions using keyword/vector hybrid retrieval.

## Business purpose

Operational guidance is often distributed across long runbooks and
architecture documents. This example combines lexical matching with semantic
similarity and role filters so relevant, authorized sections can be retrieved
for an operational question.

## Key components

- `hybrid_rag_rrf.py` initializes the `document_chunks` schema, chunks
  Markdown by headings, embeds content with Sentence Transformers, and fuses
  keyword and vector rankings with reciprocal-rank fusion.
- `paymentrunbook.md` is an example Markdown document for ingestion and
  retrieval.
- `requirements.txt` lists PostgreSQL/pgvector, embedding, and Groq client
  dependencies.

Candidate rows are filtered by `allowed_roles` in both retrieval paths. When
called from an application, pass the role from verified Day 4 JWT claims; the
CLI's `--role` value is only suitable for a local demonstration.
Questions and retrieved context are scrubbed using the Day 17 redaction
helper before they are sent to Groq.

## Setup and use

Install dependencies and configure `DATABASE_URL` for a PostgreSQL database
with permission to install/use pgvector, plus `GROQ_API_KEY` for answer
generation. The answer path also uses the Day 17 Presidio helper and its
English spaCy model:

```bash
python -m pip install -r day15_16_hybrid_search_rag/requirements.txt
python -m pip install -r day17_rbac_pii_redaction/requirements.txt
python -m spacy download en_core_web_lg
python -m day15_16_hybrid_search_rag.hybrid_rag_rrf init
python -m day15_16_hybrid_search_rag.hybrid_rag_rrf ingest \
  day15_16_hybrid_search_rag/paymentrunbook.md \
  --doc-id payments-v1 \
  --service-name payments \
  --allowed-role ops_viewer
python -m day15_16_hybrid_search_rag.hybrid_rag_rrf ask \
  "How do I investigate ERR_SSL_09?" \
  --role ops_viewer
```

The default embedding model is `sentence-transformers/all-MiniLM-L6-v2`;
`GROQ_MODEL` optionally selects an available Groq model. Re-running `ingest`
for a `doc_id` replaces that document's existing chunks.

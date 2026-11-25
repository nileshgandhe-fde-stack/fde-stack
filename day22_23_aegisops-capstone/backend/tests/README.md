# Backend Tests

## Overview

This directory contains the pytest suite for the AegisOps backend package.

## Business purpose

The tests protect API and service behavior, including data loading,
redaction-before-indexing, role handling, and assistant response behavior.

## Key components

- `test_assistant.py` exercises assistant retrieval and response behavior.
- `test_ingestion.py` checks deterministic synthetic data, DuckDB loading, and
  PII redaction before embedding/vector-store ingestion.

Run the suite from the capstone project root with
`python -m pytest backend/tests`.

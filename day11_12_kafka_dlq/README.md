# Day 11–12: Kafka-Style Dead-Letter Queue

## Overview

This folder contains a small Python simulation of a streaming worker that
validates event payloads and diverts malformed messages to a dead-letter
queue (DLQ) sink.

## Business purpose

In a streaming pipeline, one malformed or poison-pill event should not prevent
later valid records from being processed. The example illustrates per-message
validation and recording failure metadata for later inspection.

## Key components

- `redpanda_dlq_worker.py` defines the `StreamEvent` Pydantic model,
  representative encoded messages, a valid-event sink, and an in-memory DLQ
  sink.
- `process_message_with_dlq` decodes JSON, validates the event, and routes
  decoding or schema failures to the DLQ list while continuing the caller's
  loop.

## Run

The script requires Python and Pydantic:

```bash
python -m pip install pydantic
python redpanda_dlq_worker.py
```

## Scope and limitations

Despite the project name and the commented Redpanda commands in the script,
the executable code does not connect to Kafka or Redpanda. It processes a
hard-coded in-memory batch; both sinks are Python lists and are lost at exit.
The broker commands are illustrative manual notes, not an integrated worker
or automated test.

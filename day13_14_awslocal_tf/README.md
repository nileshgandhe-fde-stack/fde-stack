# Day 13–14: LocalStack S3-to-SQS Claims Ingestion

## Overview

This folder provisions a local S3 dropzone and SQS ingestion queue with
Terraform, then runs a Python worker that cleans uploaded CSV claim records
and upserts them into PostgreSQL.

## Business purpose

The exercise models a customer file-drop workflow: object creation events
trigger asynchronous processing, invalid rows are filtered, and failed queue
messages can be retried and eventually routed to a dead-letter queue (DLQ).
The cloud services are emulated locally by LocalStack.

## Key components

- `main.tf` creates the S3 bucket, SQS primary queue and DLQ, queue policy, and
  S3 object-created notification.
- `sqs_csv_worker.py` long-polls SQS, downloads referenced CSVs from S3,
  normalizes and validates claims with DuckDB, and upserts them with psycopg.
- `schema.sql` defines the PostgreSQL `clean_claims` table and constraints.
- `tests/test_sqs_csv_worker.py` covers event decoding, transformation, and
  message acknowledgement behavior.

## Data flow

The clean table follows the existing warehouse contract:
`claim_id`, `tenant_id`, `amount_usd`, `claim_status`, and `updated_at`.
Identifiers and status values are normalized; empty IDs/tenants, invalid or
non-positive amounts, unknown statuses, and invalid timestamps are discarded.
For each claim ID, the newest timestamp in the CSV wins. A database upsert also
prevents an older file from overwriting a newer stored row.

## Run locally

### Provision LocalStack resources

Start LocalStack with S3 and SQS available at `http://localhost:4566`, then run
from this directory:

```bash
terraform init
terraform apply
```

Terraform creates the bucket, the primary queue and DLQ, permits S3 to publish
to the queue, and configures `s3:ObjectCreated:*` notifications.

### Configure and run the worker

Install the worker dependencies into your Python environment:

```bash
python -m pip install -r requirements.txt
```

Set the queue URL from Terraform and the pooled `DATABASE_URL` for your Neon
branch. The LocalStack endpoint and credentials default to `localhost:4566`
and `test`:

```bash
export SQS_QUEUE_URL="$(terraform output -raw sqs_ingest_url)"
export DATABASE_URL="postgresql://..."
python sqs_csv_worker.py
```

Optional settings are `AWS_REGION`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT_URL`, `S3_ENDPOINT_URL`,
`SQS_ENDPOINT_URL`, and `LOG_LEVEL`. The worker defaults its AWS endpoints to
LocalStack; set the endpoint variables appropriately if running outside the
local stack.

The worker creates `clean_claims` from `schema.sql` if it does not exist. It
commits database writes before deleting an SQS message. Failed messages are
left unacknowledged and will be retried by SQS, then routed to the configured
DLQ after three receives.

### Upload a CSV

In another terminal, upload a claims CSV with the columns `claim_id`,
`tenant_id`, `amount_usd`, `status`, and `updated_at`. An optional
`patient_ref` column is ignored, matching the warehouse staging model.

```bash
aws --endpoint-url=http://localhost:4566 s3 ls
aws --endpoint-url=http://localhost:4566 s3 cp claims.csv \
  s3://enterprise-client-dropzone/incoming/claims.csv
```

The S3 event automatically enqueues the object reference; the worker reads the
CSV directly from S3 rather than polling the bucket.

### Tests

```bash
python -m unittest discover -s tests -v
```

The worker expects `SQS_QUEUE_URL` and `DATABASE_URL`. By default, AWS client
endpoints use LocalStack at `http://localhost:4566`; credentials default to
LocalStack's `test` values. Use a non-production database for this exercise.

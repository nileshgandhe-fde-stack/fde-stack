# LocalStack S3-to-SQS claims worker

This exercise connects the LocalStack S3 dropzone to its SQS ingest queue. The
worker long-polls the queue, downloads each newly created CSV, cleans and
deduplicates claim records in DuckDB, and upserts them into Neon Postgres.

The clean table follows the existing warehouse contract:
`claim_id`, `tenant_id`, `amount_usd`, `claim_status`, and `updated_at`.
Identifiers and status values are normalized; empty IDs/tenants, invalid or
non-positive amounts, unknown statuses, and invalid timestamps are discarded.
For each claim ID, the newest timestamp in the CSV wins. A database upsert also
prevents an older file from overwriting a newer stored row.

## 1. Provision the LocalStack resources

Start LocalStack with S3 and SQS available at `http://localhost:4566`, then run
from this directory:

```bash
terraform init
terraform apply
```

Terraform creates the bucket, the primary queue and DLQ, permits S3 to publish
to the queue, and configures `s3:ObjectCreated:*` notifications.

## 2. Configure and run the worker

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

## 3. Upload a CSV

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

## Tests

```bash
python -m unittest discover -s tests -v
```

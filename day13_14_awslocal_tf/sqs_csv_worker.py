import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote_plus

import boto3
import duckdb
import psycopg

logger = logging.getLogger(__name__)
LOCALSTACK_ENDPOINT = "http://localhost:4566"

CLEAN_CLAIMS_QUERY = """
WITH raw_claims AS (
    SELECT
        UPPER(TRIM(claim_id)) AS claim_id,
        LOWER(TRIM(tenant_id)) AS tenant_id,
        TRY_CAST(NULLIF(TRIM(amount_usd), '') AS DECIMAL(12, 2)) AS amount_usd,
        UPPER(TRIM(status)) AS claim_status,
        TRY_CAST(NULLIF(TRIM(updated_at), '') AS TIMESTAMP) AS updated_at
    FROM read_csv_auto(
        ?,
        header = true,
        all_varchar = true,
        ignore_errors = true,
        null_padding = true
    )
),
valid_claims AS (
    SELECT claim_id, tenant_id, amount_usd, claim_status, updated_at
    FROM raw_claims
    WHERE claim_id IS NOT NULL
      AND claim_id <> ''
      AND tenant_id IS NOT NULL
      AND tenant_id <> ''
      AND amount_usd > 0
      AND claim_status IN ('PENDING', 'APPROVED', 'DENIED', 'ESCALATED')
      AND updated_at IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY claim_id
        ORDER BY updated_at DESC
    ) = 1
)
SELECT claim_id, tenant_id, amount_usd, claim_status, updated_at
FROM valid_claims
ORDER BY claim_id
"""

UPSERT_CLAIMS_QUERY = """
INSERT INTO clean_claims (claim_id, tenant_id, amount_usd, claim_status, updated_at)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (claim_id) DO UPDATE SET
    tenant_id = EXCLUDED.tenant_id,
    amount_usd = EXCLUDED.amount_usd,
    claim_status = EXCLUDED.claim_status,
    updated_at = EXCLUDED.updated_at
WHERE EXCLUDED.updated_at >= clean_claims.updated_at
"""


@dataclass(frozen=True)
class Settings:
    queue_url: str
    database_url: str
    region: str
    s3_endpoint_url: str
    sqs_endpoint_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        queue_url = os.environ.get("SQS_QUEUE_URL")
        database_url = os.environ.get("DATABASE_URL")
        if not queue_url:
            raise ValueError("SQS_QUEUE_URL must be set")
        if not database_url:
            raise ValueError("DATABASE_URL must be set")

        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        default_endpoint = os.environ.get("AWS_ENDPOINT_URL", LOCALSTACK_ENDPOINT)
        return cls(
            queue_url=queue_url,
            database_url=database_url,
            region=region,
            s3_endpoint_url=os.environ.get("S3_ENDPOINT_URL", default_endpoint),
            sqs_endpoint_url=os.environ.get("SQS_ENDPOINT_URL", default_endpoint),
        )


def create_aws_clients(settings: Settings) -> tuple[Any, Any]:
    session = boto3.Session(
        region_name=settings.region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    )
    s3 = session.client("s3", endpoint_url=settings.s3_endpoint_url)
    sqs = session.client("sqs", endpoint_url=settings.sqs_endpoint_url)
    return s3, sqs


def extract_csv_objects(message_body: str) -> list[tuple[str, str]]:
    event = json.loads(message_body)
    if event.get("Event") == "s3:TestEvent":
        return []

    records = event.get("Records")
    if not isinstance(records, list):
        raise ValueError("SQS message does not contain S3 event Records")

    objects: list[tuple[str, str]] = []
    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        if key.lower().endswith(".csv"):
            objects.append((bucket, key))
    return objects


def transform_csv(csv_path: str | Path) -> list[tuple[Any, ...]]:
    with duckdb.connect(database=":memory:") as connection:
        return connection.execute(CLEAN_CLAIMS_QUERY, [str(csv_path)]).fetchall()


def download_and_transform(s3_client: Any, bucket: str, key: str) -> list[tuple[Any, ...]]:
    with tempfile.TemporaryDirectory(prefix="sqs-csv-worker-") as directory:
        csv_path = Path(directory) / "source.csv"
        response = s3_client.get_object(Bucket=bucket, Key=key)
        with response["Body"] as body, csv_path.open("wb") as output:
            shutil.copyfileobj(body, output)
        return transform_csv(csv_path)


def ensure_schema(connection: psycopg.Connection[Any]) -> None:
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with connection.transaction():
        connection.execute(schema)


def process_message(
    message_body: str,
    s3_client: Any,
    connection: psycopg.Connection[Any],
) -> int:
    objects = extract_csv_objects(message_body)
    clean_records: list[tuple[Any, ...]] = []
    for bucket, key in objects:
        logger.info("Downloading s3://%s/%s", bucket, key)
        clean_records.extend(download_and_transform(s3_client, bucket, key))

    if clean_records:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.executemany(UPSERT_CLAIMS_QUERY, clean_records)

    return len(clean_records)


def run_worker(
    settings: Settings,
    s3_client: Any,
    sqs_client: Any,
    connection: psycopg.Connection[Any],
) -> None:
    while True:
        response = sqs_client.receive_message(
            QueueUrl=settings.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=300,
        )

        for message in response.get("Messages", []):
            message_id = message["MessageId"]
            logger.info("Processing SQS message %s", message_id)
            record_count = process_message(message["Body"], s3_client, connection)
            sqs_client.delete_message(
                QueueUrl=settings.queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            logger.info("Processed SQS message %s (%d clean records)", message_id, record_count)


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    s3_client, sqs_client = create_aws_clients(settings)
    with psycopg.connect(settings.database_url) as connection:
        ensure_schema(connection)
        run_worker(settings, s3_client, sqs_client, connection)


if __name__ == "__main__":
    main()

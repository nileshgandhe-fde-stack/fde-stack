import io
import json
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, Mock

from sqs_csv_worker import Settings, extract_csv_objects, run_worker, transform_csv


class ExtractCsvObjectsTests(unittest.TestCase):
    def test_decodes_s3_url_encoded_key(self) -> None:
        body = json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": "dropzone"},
                            "object": {"key": "incoming%2Fclient+claims.csv"},
                        }
                    }
                ]
            }
        )

        self.assertEqual(
            extract_csv_objects(body),
            [("dropzone", "incoming/client claims.csv")],
        )

    def test_s3_test_event_has_no_objects(self) -> None:
        self.assertEqual(extract_csv_objects('{"Event":"s3:TestEvent"}'), [])


class TransformCsvTests(unittest.TestCase):
    def test_normalizes_filters_and_deduplicates_claims(self) -> None:
        csv_content = (
            "claim_id,tenant_id,patient_ref,amount_usd,status,updated_at\n"
            "clm-1, ACME ,PAT-1,12.50,pending,2026-10-01 09:00:00\n"
            "CLM-1,Acme,PAT-1,12.50,approved,2026-10-02 09:00:00\n"
            "CLM-2,Globex,PAT-2,-5.00,denied,2026-10-02 09:00:00\n"
            "CLM-3,Globex,PAT-3,20.00,unknown,2026-10-02 09:00:00\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "claims.csv"
            csv_path.write_text(csv_content, encoding="utf-8")

            records = transform_csv(csv_path)

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0],
            (
                "CLM-1",
                "acme",
                Decimal("12.50"),
                "APPROVED",
                datetime(2026, 10, 2, 9, 0),
            ),
        )


class WorkerDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            queue_url="http://localhost:4566/000000000000/claims",
            database_url="postgresql://unused",
            region="us-east-1",
            s3_endpoint_url="http://localhost:4566",
            sqs_endpoint_url="http://localhost:4566",
        )
        self.message = {
            "MessageId": "message-1",
            "ReceiptHandle": "receipt-1",
            "Body": json.dumps(
                {
                    "Records": [
                        {
                            "s3": {
                                "bucket": {"name": "dropzone"},
                                "object": {"key": "claims.csv"},
                            }
                        }
                    ]
                }
            ),
        }

    def test_acknowledges_message_after_successful_database_write(self) -> None:
        s3 = Mock()
        s3.get_object.return_value = {
            "Body": io.BytesIO(
                b"claim_id,tenant_id,amount_usd,status,updated_at\n"
                b"clm-1,acme,12.50,approved,2026-10-02 09:00:00\n"
            )
        }
        queue = Mock()
        queue.receive_message.side_effect = [
            {"Messages": [self.message]},
            RuntimeError("stop polling"),
        ]
        connection = MagicMock()

        with self.assertRaisesRegex(RuntimeError, "stop polling"):
            run_worker(self.settings, s3, queue, connection)

        connection.cursor.return_value.__enter__.return_value.executemany.assert_called_once()
        queue.delete_message.assert_called_once_with(
            QueueUrl=self.settings.queue_url,
            ReceiptHandle="receipt-1",
        )

    def test_does_not_acknowledge_message_when_download_fails(self) -> None:
        s3 = Mock()
        s3.get_object.side_effect = OSError("S3 unavailable")
        queue = Mock()
        queue.receive_message.return_value = {"Messages": [self.message]}

        with self.assertRaisesRegex(OSError, "S3 unavailable"):
            run_worker(self.settings, s3, queue, Mock())

        queue.delete_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()

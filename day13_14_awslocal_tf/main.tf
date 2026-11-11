terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3  = "http://localhost:4566"
    sqs = "http://localhost:4566"
  }
}

# 1. Dead Letter Queue for failed flat-file ingestions
resource "aws_sqs_queue" "ingest_dlq" {
  name = "enterprise-flatfile-dlq"
}

# 2. Primary Ingestion SQS Queue wired to DLQ after 3 failed attempts
resource "aws_sqs_queue" "ingest_queue" {
  name                       = "enterprise-flatfile-ingest"
  visibility_timeout_seconds = 300
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingest_dlq.arn
    maxReceiveCount     = 3
  })
}

data "aws_iam_policy_document" "allow_s3_to_send_ingest_events" {
  statement {
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.ingest_queue.arn]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.dropzone.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "allow_s3_to_send_ingest_events" {
  queue_url = aws_sqs_queue.ingest_queue.id
  policy    = data.aws_iam_policy_document.allow_s3_to_send_ingest_events.json
}

# 3. Client S3 Dropzone Bucket
resource "aws_s3_bucket" "dropzone" {
  bucket = "enterprise-client-dropzone"
}

resource "aws_s3_bucket_notification" "dropzone_created_objects" {
  bucket = aws_s3_bucket.dropzone.id

  queue {
    queue_arn = aws_sqs_queue.ingest_queue.arn
    events    = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_sqs_queue_policy.allow_s3_to_send_ingest_events]
}

output "s3_dropzone_bucket" {
  value = aws_s3_bucket.dropzone.bucket
}

output "sqs_ingest_url" {
  value = aws_sqs_queue.ingest_queue.id
}
# Worker Tests

## Overview

This directory contains the unit tests for the LocalStack S3-to-SQS claims
worker.

## Business purpose

The tests check that S3 notifications are decoded correctly, CSV rows are
normalized and filtered, and queue messages are acknowledged only after
processing succeeds.

## Run

From `day13_14_awslocal_tf/`, run
`python -m unittest discover -s tests -v`.

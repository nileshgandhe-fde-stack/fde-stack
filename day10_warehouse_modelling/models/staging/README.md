# Staging Models

## Overview

This directory contains the dbt staging view and its source/model contract.

## Business purpose

The staging layer converts a legacy claims feed into one normalized,
deduplicated row per claim, providing a stable relation for downstream
analytics.

## Key components

- `stg_enterprise_claims.sql` normalizes claim IDs, tenant IDs, statuses,
  amounts, and timestamps; it filters null IDs and non-positive amounts and
  keeps the latest timestamp per claim.
- `schema.yml` declares the `legacy_erp.raw_claims` source and tests the
  staged model's required fields, unique claim IDs, and accepted statuses.

The source relation must exist in the configured dbt target; the CSV in the
project's `seeds/` directory is not automatically substituted for that source.

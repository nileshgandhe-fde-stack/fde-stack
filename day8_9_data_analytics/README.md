# Day 8-9: Data Analytics and Dirty Data Cleaning

## Overview
This module demonstrates how to clean and normalize messy enterprise data using DuckDB and SQL-first transformation patterns. It focuses on the common operational problem of dirty datasets that contain duplicates, inconsistent casing, missing normalization, and invalid numeric values.

## Business purpose
Operational analytics often starts with data that is technically readable but not trustworthy. In real enterprise environments, upstream systems may emit:
- duplicate records for the same claim or incident
- inconsistent naming conventions across tenant IDs
- negative or corrupt amounts
- mixed-status values and timestamp formatting issues

This exercise shows a pragmatic approach to turning noisy raw data into a clean and queryable analytic dataset.

## Key components

### Dirty data source
The script begins by creating a raw CSV file named `dirty_claims.csv` with intentionally messy claim data. The examples include:
- repeated `claim_id` values across multiple rows
- tenant values written in different cases
- amounts that include invalid negative values
- status names that are inconsistent or semantically noisy

### DuckDB processing pipeline
The data is loaded into an in-memory DuckDB database and transformed in a single SQL pipeline.

The workflow includes:
- `read_csv_auto('dirty_claims.csv', ignore_errors=true)` for tolerant ingestion
- `TRIM` and `UPPER`/`LOWER` normalization on raw fields
- `CAST` conversion for numeric and timestamp safety
- `WHERE CAST(amount_usd AS DOUBLE) > 0` to remove corrupt or invalid amounts
- `QUALIFY ROW_NUMBER() OVER (PARTITION BY ...) = 1` to keep only the latest record per claim

### Output artifact
The cleaned data is written to:
- `clean_claims.parquet`

This makes the normalized result suitable for downstream analytics, dashboards, and automated reporting.

## Data cleaning logic
The script performs the following transformations:
1. Standardizes `claim_id` values to uppercase and strips whitespace.
2. Normalizes `tenant_id` values to lowercase for consistent grouping.
3. Converts `amount_usd` to a numeric double value and discards invalid negative or broken entries.
4. Normalizes `status` values to uppercase.
5. Parses `updated_at` as a proper timestamp.
6. Deduplicates records using the most recent version of each claim based on timestamp.

## Example transformation
A raw duplicate set like this:

```text
CLM-100,Acme_Health,PAT-991,1250.50,PENDING,2026-10-01 09:00:00
CLM-100,ACME_HEALTH,PAT-991,1250.50,APPROVED,2026-10-02 14:30:00
```

is normalized to one canonical latest row:

```text
CLM-100,acme_health,PAT-991,1250.50,APPROVED,2026-10-02 14:30:00
```

## Query and output flow
1. Raw CSV is created with realistic dirty values.
2. DuckDB ingests the file using tolerant CSV parsing.
3. SQL applies sanitization and deduplication logic.
4. The final cleaned dataset is exported to Parquet.
5. The script prints the result as a DataFrame for quick validation.

## Run it
From this folder:

```bash
python dirty_data_duckdb.py
```

This will generate:
- `dirty_claims.csv`
- `clean_claims.parquet`

## Best use cases
- data quality engineering
- analytics pipeline preparation
- client-facing data normalization for reporting
- SQL-based rule validation and duplicate removal

## Notes
This folder is intentionally lightweight but realistic. It demonstrates the kind of first-pass data hygiene work often required before building serious analytics or operational insights from enterprise datasets.

# Day 10: Warehouse Modelling with dbt and DuckDB

## Overview
This module demonstrates a lightweight data warehouse modelling workflow using dbt and DuckDB. It focuses on cleaning, normalizing, and validating raw enterprise claims before exposing them as a trusted staging model for downstream analytics.

## Business purpose
Data warehouses are only useful when the upstream data is trusted. In enterprise systems, raw data often includes:
- duplicate claims
- inconsistent tenant naming
- invalid negative amounts
- inconsistent status casing
- mixed or messy timestamps

This project shows how to turn that noisy source data into a reliable staging layer with repeatable transformations and automated validation tests.

## Key components

### dbt project root
The project is configured with `dbt_project.yml`, which defines:
- the project name and version
- the model and seed paths
- the profile name used for local DuckDB execution
- the default materialization strategy for staging models

### Source data
The source is represented as a raw claims table loaded from a seeded CSV in `seeds/raw_claims.csv`.

This seeded data simulates an enterprise ERP feed and includes realistic data-quality issues such as:
- duplicate claim IDs
- mixed-case tenant names
- negative or invalid monetary values
- status values that require normalization

### Staging model
The SQL file `models/staging/stg_enterprise_claims.sql` creates a view called `stg_enterprise_claims`.

It performs the following transformations:
- uppercase claim IDs
- lowercase tenant IDs
- numeric casting for amount values
- uppercase status normalization
- timestamp casting
- deduplication using `ROW_NUMBER()` over claim ID partitioning
- filtering of invalid rows, such as negative amounts or null claim IDs

### Schema and tests
The schema file `models/staging/schema.yml` defines:
- the source table contract for `legacy_erp.raw_claims`
- tests for nullability and accepted values
- model-level constraints such as uniqueness and required fields

These tests protect the raw-to-staging contract and validate that the transformed model stays trustworthy.

The project expects dbt Core and the `dbt-duckdb` adapter, plus a local dbt
profile named `day10_warehouse_modelling` that points at DuckDB. Profile
credentials live outside this folder (normally in `~/.dbt/profiles.yml`).
The repository does not include that profile.

Install the dbt packages with `python -m pip install dbt-core dbt-duckdb`
before running the commands below.

## Transformation flow
1. Raw seed data is loaded into DuckDB.
2. The staging model reads from the `legacy_erp.raw_claims` source.
3. Duplicate records are resolved by selecting the latest row per claim ID.
4. Invalid values are filtered out before the final view is exposed.
5. dbt tests validate the resulting model against the expected contract.

## Example normalized output
The staging model produces rows with:
- normalized claim IDs
- normalized tenant names
- valid numeric claim amounts
- normalized status values
- deduplicated latest records by claim ID

## Run it
From the project directory:

```bash
dbt seed --profiles-dir ~/.dbt
dbt build --profiles-dir ~/.dbt
```

`dbt build` runs the seed/model build and the declared tests. To run individual
phases:

```bash
dbt compile --profiles-dir ~/.dbt
dbt test --profiles-dir ~/.dbt
```

The staging model reads the `legacy_erp.raw_claims` source declared in
`models/staging/schema.yml`; configure or load that source in the selected
DuckDB profile before running the model. The checked-in `seeds/raw_claims.csv`
is a seed file, not the declared raw source table.

## Best use cases
- staging-layer design for warehouse pipelines
- contract testing for upstream data quality
- lightweight warehouse modelling in local environments
- demo data validation before downstream BI consumption

## Notes
This folder is intentionally simple and focused on the core dbt workflow: source ingestion, model transformation, contract validation, and trustworthy data exposure for analytics consumers.

# FDE Stack

This repository contains a small set of learning-focused service examples covering API design, resilience engineering, and identity/security patterns.

## Project structure

- [day1_2_fastapi](day1_2_fastapi) — FastAPI ingestion API with structured logging, validation, and correlation IDs.
- [day1_2_fastapi/README.md](day1_2_fastapi/README.md) — technical documentation for the ingestion API.
- [day3_flaky_legacy](day3_flaky_legacy) — resilience patterns for flaky legacy integrations using retries and circuit breaking.
- [day3_flaky_legacy/README.md](day3_flaky_legacy/README.md) — technical documentation for the legacy integration simulation.
- [day4_oidc_and_rbac](day4_oidc_and_rbac) — JWT-based authentication and role-based access control for protected endpoints.
- [day4_oidc_and_rbac/README.md](day4_oidc_and_rbac/README.md) — technical documentation for the OIDC/RBAC gateway.
- [day5_7_ops_ui](day5_7_ops_ui) — Streamlit operations console for triage, RBAC-aware actions, and live incident views.
- [day5_7_ops_ui/README.md](day5_7_ops_ui/README.md) — technical documentation for the operations UI dashboard.
- [day8_9_data_analytics](day8_9_data_analytics) — DuckDB-powered data cleanup, deduplication, and analytics preparation for noisy enterprise data.
- [day8_9_data_analytics/README.md](day8_9_data_analytics/README.md) — technical documentation for the dirty-data cleaning workflow.
- [day10_warehouse_modelling](day10_warehouse_modelling) — dbt-based warehouse modelling and staging-layer validation for enterprise claim data.
- [day10_warehouse_modelling/README.md](day10_warehouse_modelling/README.md) — technical documentation for the dbt warehouse modelling project.
- [day13_14_awslocal_tf](day13_14_awslocal_tf) — LocalStack S3-to-SQS CSV ingestion, DuckDB cleanup, and Neon Postgres loading.
- [day13_14_awslocal_tf/README.md](day13_14_awslocal_tf/README.md) — setup and run instructions for the local claims worker.

## Learning goals

1. Build a well-structured API with FastAPI.
2. Normalize noisy upstream data before persistence.
3. Add request tracing and observability to the service edge.
4. Harden integrations against flaky legacy dependencies.
5. Implement JWT verification and RBAC policy enforcement.

## How to use this repository

Each folder is designed as a standalone exercise. Open the README in the relevant folder for a deeper description of the application flow, important components, and runtime instructions.

## Notes

This is a study-oriented repository intended for hands-on experimentation and learning rather than as a full production deployment stack.

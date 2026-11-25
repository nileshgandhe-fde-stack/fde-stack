# dbt Seeds

## Overview

This directory contains the CSV seed data used by the Day 10 dbt project.

## Business purpose

The seed gives the project a small local claims dataset for demonstrating dbt
seed loading and staging transformations.

## Key components

- `raw_claims.csv` contains the sample claim records.
- `dbt seed` loads the CSV into the configured dbt target.

The staging model currently reads the separately declared
`legacy_erp.raw_claims` source. Configure that source relation in the target;
loading the seed alone does not make the model source reference point to it.

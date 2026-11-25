# dbt Models

## Overview

This directory contains SQL models organized by dbt layer.

## Business purpose

The models turn source data into consistent relations for analytics consumers,
with the current project focused on a single claims staging view.

## Key components

- `staging/` contains the enterprise claims staging view and its schema/tests.

Run models from the project root using the configured dbt profile described in
the project README.

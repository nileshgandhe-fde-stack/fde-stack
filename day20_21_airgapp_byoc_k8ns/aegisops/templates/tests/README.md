# Helm Release Tests

## Overview

This folder contains Helm test hooks for the chart scaffold.

## Key components

- `test-connection.yaml` defines a test pod intended to check access to the
  chart's service after installation.

It is a template-level smoke check, not an end-to-end AegisOps test.

# AegisOps Helm Deployment Area

## Overview

This directory reserves a location for a future AegisOps Helm chart. It
currently has no chart files or release configuration.

## Business purpose

A dedicated deployment area can hold Kubernetes packaging independently from
the application implementation.

## Key components

- `helm/` is an empty placeholder directory with its own README.
- No `Chart.yaml`, values, or templates are present here, so Helm cannot
  install the capstone from this directory.
- See the separate starter chart in
  `day20_21_airgapp_byoc_k8ns/aegisops/`.

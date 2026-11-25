# Deployment

## Overview

This directory is reserved for deployment assets for the AegisOps capstone.
The current `helm/` subtree is a placeholder and does not contain a deployable
chart.

## Business purpose

Keeping deployment configuration separate provides a home for future
environment-specific packaging and release resources without coupling them to
application code.

## Key components

- `helm/` contains a `.gitkeep` and a nested placeholder README; it has no
  `Chart.yaml`, values, or templates.
- The BYOC/Kubernetes learning scaffold is maintained separately in
  `../../day20_21_airgapp_byoc_k8ns/`.

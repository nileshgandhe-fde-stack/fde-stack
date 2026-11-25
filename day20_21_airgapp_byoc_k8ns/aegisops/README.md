# BYOC Helm Chart Scaffold

## Overview

This directory contains a Helm application-chart scaffold named `aegisops`.
It is a generic starting point and does not package or configure the AegisOps
capstone application.

## Business purpose

The chart demonstrates common Kubernetes packaging hooks—deployments,
services, optional ingress routes, service accounts, and autoscaling—that can
be parameterized for a customer-controlled environment.

## Key components

- `Chart.yaml` identifies chart version `0.1.0` and app version `1.16.0`.
- `values.yaml` sets a single replica, `nginx` image, ClusterIP service, and
  disabled ingress, HTTPRoute, and autoscaling defaults.
- `templates/` renders the workload, service, service account, optional
  ingress/HTTPRoute/HPA, and a connection test.

## Validate

From the parent folder, run `helm lint aegisops` and
`helm template aegisops aegisops` to inspect the rendered scaffold. Review
image, security context, probes, networking, secrets, and storage settings
before deploying to a real cluster.

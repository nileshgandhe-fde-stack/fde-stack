# Day 20–21: BYOC and Air-Gap Kubernetes Exercise

## Overview

This folder contains a Zarf package definition, a Kubernetes manifest with
default-deny network policies, a Kind cluster configuration, and a starter
Helm chart. These files are deployment exercises; they are not a complete
deployment of the AegisOps application.

## Business purpose

Customer-controlled and disconnected environments require teams to stage
images and configuration in advance and to restrict pod-to-pod traffic. This
module illustrates offline packaging concepts and a namespace network policy
that permits only selected UI-to-API, API-to-Postgres, and DNS flows.

## Key components

- `zarf.yaml` declares a Zarf package containing the hardened Kubernetes
  manifest and image references for `python:3.11-slim`, `postgres:15-alpine`,
  and `nginx:alpine`.
- `k8s-hardened-byoc.yaml` defines placeholder Postgres, API, and UI
  deployments/services. The API container runs Python's built-in HTTP server;
  the UI is stock Nginx. Neither is the AegisOps backend or Streamlit UI.
- `k8s-hardened-byoc.yaml` also contains four NetworkPolicies: namespace-wide
  default deny, UI egress to API and DNS, API ingress from UI plus egress to
  Postgres and DNS, and Postgres ingress from API.
- [`aegisops/`](aegisops/) is a generic Helm chart scaffold. Its default image
  is Nginx; ingress, HTTPRoute, and autoscaling are disabled by default.
- `kind-config.yaml` defines a two-node Kind cluster with its default CNI
  disabled. Install a compatible CNI before relying on NetworkPolicy
  enforcement.

## Important limitations

This is a teaching scaffold, not a production-ready or verified air-gap
deployment. The Kubernetes YAML includes a hard-coded demonstration database
password, the API/UI workloads are placeholders, and the Zarf image list is
not wired into the Helm chart. Replace these examples with reviewed
application images, managed secrets, storage, probes, and deployment settings
before using any real environment.

NetworkPolicies require a CNI that enforces them. The policies allow DNS to the
`kube-system` namespace on port 53; verify the labels and DNS topology used by
the target cluster.

## Validate the manifests

From this directory, render/lint the Helm scaffold:

```bash
helm lint aegisops
helm template aegisops aegisops
```

Inspect the plain Kubernetes manifest before applying it:

```bash
kubectl apply --dry-run=client -f k8s-hardened-byoc.yaml
```

The Kind configuration requires a CNI plugin to be installed after cluster
creation. Zarf packaging/deployment also requires the Zarf CLI and a
compatible Kubernetes cluster; commands should be adapted to the target
environment and reviewed before execution.

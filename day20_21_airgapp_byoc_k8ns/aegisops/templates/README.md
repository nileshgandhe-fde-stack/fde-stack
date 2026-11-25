# Helm Templates

## Overview

This directory contains the Helm templates rendered by the BYOC chart.

## Key components

- `_helpers.tpl` defines reusable chart names and labels.
- `deployment.yaml`, `service.yaml`, and `serviceaccount.yaml` create the
  default workload and service identity.
- `ingress.yaml` and `httproute.yaml` are conditional exposure options.
- `hpa.yaml` renders autoscaling only when enabled.
- `tests/test-connection.yaml` defines a Helm release connectivity test.

The deployment uses chart values and defaults to the sample Nginx image; these
templates do not deploy the AegisOps application itself.

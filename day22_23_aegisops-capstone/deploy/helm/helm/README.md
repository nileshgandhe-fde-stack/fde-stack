# Helm Directory

## Overview

This directory is a placeholder for Helm-related deployment content. It
currently contains no chart metadata, templates, or values files.

## Business purpose

The capstone keeps its Helm deployment area separate from the application
source so a deployment chart can be added without mixing it with backend or
UI code.

## Key components

- This README is the only tracked file in this directory.
- The sibling `deploy/helm/` directory is also a placeholder; no deployable
  Helm release is provided here.

Do not treat this directory as a working chart. The independent chart scaffold
for the BYOC exercise is in
[`day20_21_airgapp_byoc_k8ns/aegisops`](../../../../day20_21_airgapp_byoc_k8ns/aegisops/README.md).
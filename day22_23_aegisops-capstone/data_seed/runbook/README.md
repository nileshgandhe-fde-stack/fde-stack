# Example Runbooks

## Overview

This directory contains Markdown operational runbooks supplied as static
retrieval examples for the AegisOps project.

## Business purpose

Runbooks provide procedural evidence for incident questions and let the
assistant retrieve troubleshooting guidance without relying on generated
post-mortems.

## Key components

- `connection-pool-saturation.md` covers investigation of database pool
  pressure.
- `retry-storm.md` covers retry amplification and recovery.
- `worker-capacity.md` covers worker scaling and recovery signals.

These are authored examples; `seed_enterprise_data.py` does not generate them.
To use this folder with the API, set `RUNBOOKS_DIR=data_seed/runbook`.

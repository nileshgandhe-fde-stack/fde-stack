# Day 5-7: Operations UI and Triage Console

## Overview
This module provides the operational dashboard for the FDE stack. It is a lightweight Streamlit application that presents a role-aware incident view for enterprise operators, security analysts, and administrators. The interface is designed to simulate an internal operations console for triaging active incidents and executing remediation workflows.

## Business purpose
In real enterprise environments, operations teams need a single place to:
- understand live incident health
- filter by tenant and severity
- see key SLAs and latency indicators
- trigger controlled remediation actions according to RBAC policy

The dashboard acts as the human-facing layer above the backend automation and security patterns demonstrated in the other modules.

## Key components

### Streamlit application
The dashboard is implemented in `dashboard.py` and uses Streamlit for a responsive web UI.

Main sections include:
- sidebar role and tenant controls
- KPI summary cards
- live incident queue table
- runbook execution panel

### Session context and role simulation
The sidebar lets the simulated operator choose a role from:
- `fde_admin`
- `sec_auditor`
- `ops_viewer`

It also provides tenant filters so the console can focus on a subset of client environments, including:
- `acme_health`
- `globex_fin`
- `initech_erp`

This simulates identity-aware operational access without a full authentication integration.

### Incident telemetry model
The dashboard reads a sample dataset stored in-memory as a Pandas DataFrame. Each row includes:
- incident ID
- tenant
- severity
- service
- latency
- status

The sample incident data is representative of a distributed operations environment with open, investigating, and resolved states.

### KPI summarization
The dashboard renders operational summary cards for:
- active incidents
- critical incident count
- p95 latency for the filtered incident set
- dead-letter / poison payload indicator status

These numbers provide quick operators’ context before action is taken.

### Runbook execution
The secondary panel allows a selected incident to be processed via an automated remediation workflow. The key security control is role enforcement:
- only `fde_admin` may trigger state-changing actions
- non-admin roles receive a `403 Forbidden`-style warning in the UI

This mirrors the RBAC model used in the earlier security module and demonstrates operational policy enforcement in a real UI workflow.

## Request / interaction flow
1. The operator chooses a role and tenant scope in the sidebar.
2. The application filters the incident queue based on the tenant selection.
3. KPI cards update to reflect the filtered workload.
4. The operator selects an incident and triggers a remediation workflow.
5. If the user is not an admin, the system blocks the action and shows an access error.
6. If the user is an admin, the workflow executes and displays a success message.

## Example UI behavior
- `ops_viewer` can inspect the incident queue but cannot trigger remediation
- `fde_admin` can execute runbooks and complete workflow actions
- filtered data updates instantly as the operator adjusts the tenant lens

## Runtime configuration
The service is configured through Docker Compose:
- container image: Python 3.11 slim
- port: `8501`
- app command: `streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0`

## Run it
From this folder:

```bash
docker compose up --build -d
```

Then open:

```text
http://localhost:8501
```

## Best use cases
- operations console prototypes
- incident triage UI training
- RBAC-aware operator workflows
- incident response simulation and runbook demos

## Notes
This module is intentionally lightweight and intentionally mock-driven. It demonstrates the structure of a modern operational dashboard without needing a live backend or production telemetry stack.

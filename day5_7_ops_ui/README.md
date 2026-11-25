# Day 5-7: Operations UI and Triage Console

## Overview
This module provides a lightweight Streamlit dashboard with sample incident
data, tenant filtering, operational KPIs, and a simulated remediation action.
It is a standalone UI exercise and does not connect to the APIs in other folders.

## Business purpose
In real enterprise environments, operations teams need a single place to:
- review incident health
- filter by tenant and severity
- see key SLAs and latency indicators
- see whether a remediation action is available to their role

This sample uses in-memory data and local role selection to demonstrate the
operator workflow; it is not connected to backend automation or security
services.

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

The selected role is only local UI state. It is not a JWT, does not call the
Day 4 gateway, and is not an authorization boundary.

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

### Simulated remediation
The secondary panel simulates processing a selected incident. The UI displays
a warning for non-admin roles and a success message for `fde_admin`; it does
not execute a real runbook or record an audit event. This UI-only check is not
a security control.

The UI displays a `403 Forbidden`-style warning unless the selected role is
`fde_admin`; selecting that role only triggers the simulated success path.

They illustrate how a role-aware workflow might be presented to an operator.

## Request / interaction flow
1. The operator chooses a simulated role and tenant scope in the sidebar.
2. The application filters the incident queue based on the tenant selection.
3. KPI cards update to reflect the filtered workload.
4. The operator selects an incident and triggers a remediation workflow.
5. If the user is not an admin, the system blocks the action and shows an access error.
6. If the selected role is `fde_admin`, the UI waits briefly and displays a
   simulated success message.

## Example UI behavior
- `ops_viewer` can inspect the sample incident queue and sees a warning if the
  remediation button is used
- `fde_admin` sees the simulated remediation success message
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
This module is intentionally mock-driven. It demonstrates dashboard layout
and interaction patterns without a live backend or production telemetry stack.

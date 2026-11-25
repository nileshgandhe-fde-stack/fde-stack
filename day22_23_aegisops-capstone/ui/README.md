# Streamlit UI

## Overview

This directory contains the Streamlit web interface for the AegisOps incident
assistant and its SRE control plane.

## Business purpose

The UI provides operators a browser-based way to ask incident questions,
inspect evidence returned by the API, and view operational telemetry.

## Key components

- `app.py` provides the role selector, demo-token request, incident question
  form, evidence display, and periodically refreshed control-plane metrics.
- `AEGISOPS_API_URL` selects the backend URL; it defaults to
  `http://localhost:8000`.

The role selector only requests a token from the API; backend authorization
remains authoritative. Demo-token issuance must not be used as production
authentication.

Start the API with the environment described in the repository README, then
launch the UI:

```sh
streamlit run ui/app.py
```

Set `AEGISOPS_API_URL` if the API is not at `http://localhost:8000`. The
Enterprise Role Switcher requests a short-lived demo JWT for SRE Lead, Tier-1
Support, or External Auditor. The API—not the browser—enforces post-mortem
visibility. Demo token issuance is not production authentication.

The SRE Control Plane refreshes API p95 latency, estimated LLM token cost,
circuit-breaker status, and PII redaction totals every ten seconds.
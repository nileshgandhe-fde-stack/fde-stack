# Streamlit UI

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
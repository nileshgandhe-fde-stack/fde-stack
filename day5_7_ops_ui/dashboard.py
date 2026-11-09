import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="FDE Week-1 Operations Console", layout="wide")

st.title("⚡ Enterprise Operations & SLA Triage Console (Week-1 MVP)")
st.caption("Forward Deployed Engineering Rapid Prototype • Role-Aware Operational View")

# Sidebar Role & Tenant Controls
with st.sidebar:
    st.header("🔐 Session Context")
    active_role = st.selectbox("Simulated JWT Role", ["fde_admin", "sec_auditor", "ops_viewer"])
    tenant_filter = st.multiselect("Client Tenants", ["acme_health", "globex_fin", "initech_erp"], default=["acme_health", "globex_fin"])
    st.info(f"Active RBAC Policy: **{active_role}**")

# Sample Operational Telemetry
data = pd.DataFrame([
    {"Incident ID": "INC-901", "Tenant": "acme_health", "Severity": "CRITICAL", "Service": "hl7-ingest-gw", "Latency (ms)": 1420, "Status": "OPEN"},
    {"Incident ID": "INC-902", "Tenant": "globex_fin", "Severity": "HIGH", "Service": "ledger-sync", "Latency (ms)": 680, "Status": "INVESTIGATING"},
    {"Incident ID": "INC-903", "Tenant": "acme_health", "Severity": "MEDIUM", "Service": "claims-pdf-ocr", "Latency (ms)": 310, "Status": "RESOLVED"},
    {"Incident ID": "INC-904", "Tenant": "initech_erp", "Severity": "CRITICAL", "Service": "sap-rfc-bridge", "Latency (ms)": 2890, "Status": "OPEN"},
])

filtered = data[data["Tenant"].isin(tenant_filter)]

# KPI Row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Incidents", len(filtered[filtered["Status"] != "RESOLVED"]), "-2 vs yesterday")
c2.metric("Critical (P1) Count", len(filtered[filtered["Severity"] == "CRITICAL"]))
c3.metric("p95 Gateway Latency", f"{int(filtered['Latency (ms)'].quantile(0.95))} ms")
c4.metric("DLQ Poison Payloads", "0", "Circuit CLOSED")

st.subheader("📋 Live Enterprise Incident Queue")
st.dataframe(filtered, use_container_width=True)

st.subheader("🛠️ Human-in-the-Loop Remediation")
selected_inc = st.selectbox("Select Incident for Automated Runbook Execution", filtered["Incident ID"])
if st.button("🚀 Trigger Auto-Remediation Workflow"):
    if active_role != "fde_admin":
        st.error(f"⛔ HTTP 403 Forbidden: Role '{active_role}' cannot execute state-mutating runbooks. Switch to 'fde_admin' in the sidebar.")
    else:
        with st.spinner(f"Executing circuit reset & pod drain for {selected_inc}..."):
            time.sleep(1.0)
        st.success(f"✅ Runbook executed for {selected_inc} by {active_role}. Audit log recorded.")
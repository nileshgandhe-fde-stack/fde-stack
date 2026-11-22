"""Streamlit UI for the AegisOps incident assistant and SRE control plane."""

from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.environ.get("AEGISOPS_API_URL", "http://localhost:8000").rstrip("/")
ROLES = {
    "SRE Lead": "sre_lead",
    "Tier-1 Support": "tier1_support",
    "External Auditor": "external_auditor",
}

st.set_page_config(page_title="AegisOps", page_icon="🛡️", layout="wide")
st.title("AegisOps Incident Assistant")
st.caption("Role-scoped incident synthesis across operational metrics and runbooks.")

with st.sidebar:
    st.header("Enterprise Role Switcher")
    role_label = st.selectbox("Active role", list(ROLES))
    role = ROLES[role_label]
    if st.session_state.get("token_role") != role:
        st.session_state.pop("access_token", None)
    if st.button("Mint demo JWT", type="primary"):
        try:
            response = requests.post(
                f"{API_URL}/api/v1/demo/token",
                json={"role": role},
                timeout=10,
            )
            response.raise_for_status()
            token_payload = response.json()
            st.session_state["access_token"] = token_payload["access_token"]
            st.session_state["token_role"] = role
            st.session_state["token_expires_at"] = token_payload["expires_at"]
        except requests.RequestException as error:
            st.error(f"Could not mint a role token: {error}")
    if st.session_state.get("access_token") and st.session_state.get("token_role") == role:
        st.success(f"JWT active for {role_label}")
        st.caption(f"Expires: {st.session_state['token_expires_at']}")
    else:
        st.info("Mint a demo JWT to call the protected API.")
    st.warning(
        "Demo role issuance is not production authentication. "
        "It must remain disabled outside a controlled demo."
    )

token = st.session_state.get("access_token")
headers = {"Authorization": f"Bearer {token}"} if token else {}
ask_tab, control_plane_tab = st.tabs(["Incident Assistant", "SRE Control Plane"])

with ask_tab:
    st.subheader("Incident root-cause synthesis")
    st.caption(
        "The assistant combines read-only SLA metrics with role-authorized Markdown "
        "runbooks and post-mortems."
    )
    with st.form("incident_question"):
        question = st.text_area(
            "Ask about an incident",
            placeholder="What likely caused the elevated 5xx rate for payments-api?",
            max_chars=4000,
        )
        submitted = st.form_submit_button("Analyze incident")
    if submitted:
        if not token:
            st.error("Mint a JWT for the selected role before submitting a question.")
        elif len(question.strip()) < 3:
            st.error("Enter a question with at least three characters.")
        else:
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/ask",
                    headers=headers,
                    json={"question": question},
                    timeout=90,
                )
                response.raise_for_status()
                result = response.json()
                st.markdown(result["answer"])
                with st.expander("Evidence and SQL"):
                    st.write("Sources:", result["sources"])
                    st.code(result["sql_query"], language="sql")
                    st.json(result["sql_results"])
            except requests.HTTPError as error:
                detail = None
                if error.response is not None:
                    try:
                        body = error.response.json()
                    except ValueError:
                        body = {}
                    if isinstance(body, dict):
                        detail = body.get("detail")
                st.error(f"Incident analysis failed: {detail or error}")
            except requests.RequestException as error:
                st.error(f"Incident analysis failed: {error}")


with control_plane_tab:
    st.subheader("SRE Control Plane")

    @st.fragment(run_every=10)
    def show_control_plane() -> None:
        if not token:
            st.info("Mint a role JWT to view protected control-plane telemetry.")
            return
        try:
            response = requests.get(
                f"{API_URL}/api/v1/control-plane",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            metrics = response.json()
        except requests.RequestException as error:
            st.error(f"Could not load control-plane telemetry: {error}")
            return

        latency = metrics["api_p95_latency_seconds"]
        latency_text = "No requests yet" if latency is None else f"{latency * 1000:.1f} ms"
        columns = st.columns(4)
        columns[0].metric("API p95 latency", latency_text)
        columns[1].metric(
            "LLM token cost",
            (
                f"${metrics['llm_cost_usd_total']:.6f}"
                if metrics["cost_pricing_configured"]
                else "Rates not configured"
            ),
            help="Estimated using LLM_INPUT_COST_PER_1M / LLM_OUTPUT_COST_PER_1M.",
        )
        columns[2].metric(
            "Circuit breaker",
            metrics["circuit_breaker_status"].upper(),
        )
        columns[3].metric(
            "PII entities redacted",
            f"{metrics['pii_entities_redacted_total']:,}",
        )

    show_control_plane()
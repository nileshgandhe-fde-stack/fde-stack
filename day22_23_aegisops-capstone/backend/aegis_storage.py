import duckdb
import re
from typing import List, Dict

class AegisOpsCoreEngine:
    def __init__(self):
        self.con = duckdb.connect(database=":memory:")
        self.pii_redacted_total = 0
        self.rbac_blocks_total = 0
        self._seed_analytical_tables()
        self.runbooks = self._seed_governed_runbooks()

    def _seed_analytical_tables(self):
        self.con.execute("""
            CREATE TABLE tenant_sla_events (
                incident_id VARCHAR,
                tenant_id VARCHAR,
                service VARCHAR,
                severity VARCHAR,
                mttr_minutes INTEGER,
                p95_latency_ms INTEGER,
                sla_breached BOOLEAN
            );
            INSERT INTO tenant_sla_events VALUES
                ('INC-4001', 'acme_health', 'hl7-fhir-gateway', 'CRITICAL', 142, 1890, true),
                ('INC-4002', 'acme_health', 'claims-db-replica', 'HIGH', 85, 920, true),
                ('INC-4003', 'globex_fin', 'swift-wire-api', 'CRITICAL', 190, 2400, true),
                ('INC-4004', 'globex_fin', 'auth-oidc-proxy', 'MEDIUM', 18, 210, false),
                ('INC-4005', 'initech_supply', 'sap-idoc-worker', 'LOW', 12, 150, false);
        """)

    def _seed_governed_runbooks(self) -> List[Dict]:
        return [
            {
                "doc_id": "RB-101",
                "title": "HL7 FHIR Gateway Connection Pool Exhaustion",
                "body": "Root Cause: Unbounded retries during EHR sync spike. Fix: ApplyPgBouncer transaction pooling and cap max_connections=20.",
                "allowed_roles": ["ops_viewer", "sec_auditor", "fde_admin"]
            },
            {
                "doc_id": "RB-102",
                "title": "SWIFT Wire API Mutual-TLS Certificate Rotation Runbook",
                "body": "Root Cause: Expired intermediate CA on envoy-egress. Fix: Trigger Vault PKI rotation and rolling restart of swift-wire-api.",
                "allowed_roles": ["sec_auditor", "fde_admin"]
            },
            {
                "doc_id": "RB-999",
                "title": "EXECUTIVE ONLY: SOC2 Audit Findings & Penalty Exposure",
                "body": "Confidential SLA penalty exposure for acme_health is $120,000 if Q4 availability drops below 99.95%.",
                "allowed_roles": ["fde_admin"]
            }
        ]

    def scrub_pii(self, text: str) -> str:
        patterns = [
            (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "<REDACTED_EMAIL>"),
            (r"\b\d{3}-\d{2}-\d{4}\b", "<REDACTED_SSN>")
        ]
        out = text
        for pat, repl in patterns:
            matches = re.findall(pat, out)
            if matches:
                self.pii_redacted_total += len(matches)
                out = re.sub(pat, repl, out)
        return out

    def query_sla_summary(self):
        return self.con.execute("""
            SELECT
                tenant_id,
                COUNT(*) AS total_incidents,
                SUM(CASE WHEN sla_breached THEN 1 ELSE 0 END) AS sla_breaches,
                ROUND(AVG(mttr_minutes), 1) AS avg_mttr_min,
                MAX(p95_latency_ms) AS peak_p95_ms
            FROM tenant_sla_events
            GROUP BY tenant_id
            ORDER BY sla_breaches DESC
        """).df()

    def search_runbooks(self, query: str, caller_role: str) -> List[Dict]:
        clean_q = self.scrub_pii(query).lower()
        results = []
        for rb in self.runbooks:
            if caller_role not in rb["allowed_roles"]:
                self.rbac_blocks_total += 1
                continue
            if any(tok in (rb["title"] + " " + rb["body"]).lower() for tok in clean_q.split() if len(tok) > 2):
                results.append(rb)
        return results

if __name__ == "__main__":
    engine = AegisOpsCoreEngine()
    print("📊 DuckDB Tenant SLA Summary:")
    print(engine.query_sla_summary().to_string(index=False))
    print("\n🔒 Runbook Search as 'ops_viewer' (RB-999 automatically blocked):")
    print(engine.search_runbooks("hl7 gateway or soc2 penalty john@acme.org 123-45-6789", caller_role="ops_viewer"))
    print(f"PII Redacted: {engine.pii_redacted_total} | RBAC Blocks: {engine.rbac_blocks_total}")
    
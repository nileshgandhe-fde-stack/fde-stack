CREATE TABLE IF NOT EXISTS clean_claims (
    claim_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    amount_usd NUMERIC(12, 2) NOT NULL CHECK (amount_usd > 0),
    claim_status TEXT NOT NULL CHECK (
        claim_status IN ('PENDING', 'APPROVED', 'DENIED', 'ESCALATED')
    ),
    updated_at TIMESTAMP NOT NULL
);

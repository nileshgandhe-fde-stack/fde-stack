import duckdb
import os

# 1. Create a realistic messy enterprise CSV dump (duplicate claim_ids, mixed casing, corrupt rows)
RAW_CSV = """claim_id,tenant_id,patient_ref,amount_usd,status,updated_at
CLM-100,Acme_Health,PAT-991,1250.50,PENDING,2026-10-01 09:00:00
CLM-100,ACME_HEALTH,PAT-991,1250.50,APPROVED,2026-10-02 14:30:00
CLM-101,Globex_Fin,PAT-882,-999.00,ERROR_NEGATIVE,2026-10-01 11:00:00
CLM-102,Globex_Fin,PAT-774,4300.00,DENIED,2026-10-03 08:15:00
CLM-102,globex_fin,PAT-774,4300.00,APPROVED,2026-10-04 16:45:00
CLM-103,Acme_Health,PAT-512,890.00,DENIED,2026-10-04 10:00:00
CLM-104,Acme_Health,PAT-512,590.00,DENIED,2026-10-04 10:00:00
CLM-105,Acme_Health,PAT-512,790.00,DENIED,2026-10-04 10:00:00
"""

with open("dirty_claims.csv", "w") as f:
    f.write(RAW_CSV)

con = duckdb.connect(database=":memory:")

# 2. FDE Secret Weapon: Deduplicate via QUALIFY + normalize strings + filter corrupt amounts in 1 SQL pass
CLEAN_QUERY = """
COPY (
    SELECT
        UPPER(TRIM(claim_id)) AS claim_id,
        LOWER(TRIM(tenant_id)) AS tenant_id,
        patient_ref,
        CAST(amount_usd AS DOUBLE) AS amount_usd,
        UPPER(TRIM(status)) AS latest_status,
        CAST(updated_at AS TIMESTAMP) AS last_updated_at
    FROM read_csv_auto('dirty_claims.csv', ignore_errors=true)
    WHERE CAST(amount_usd AS DOUBLE) > 0
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY UPPER(TRIM(claim_id))
        ORDER BY CAST(updated_at AS TIMESTAMP) DESC
    ) = 1
) TO 'clean_claims.parquet' (FORMAT PARQUET);
"""

con.execute(CLEAN_QUERY)

print("✅ Cleaned & Deduplicated Enterprise Claims Table (from Parquet):")
df = con.execute("SELECT * FROM 'clean_claims.parquet' ORDER BY claim_id").df()
print(df.to_string(index=False))
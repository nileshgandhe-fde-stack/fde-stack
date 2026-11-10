{{ config(materialized='view') }}

WITH raw_source AS (
    SELECT * FROM {{ source('legacy_erp', 'raw_claims') }}
),

deduplicated AS (
    SELECT
        UPPER(TRIM(claim_id)) AS claim_id,
        LOWER(TRIM(tenant_id)) AS tenant_id,
        CAST(amount_usd AS NUMERIC(12, 2)) AS amount_usd,
        UPPER(TRIM(status)) AS claim_status,
        CAST(updated_at AS TIMESTAMP) AS updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY UPPER(TRIM(claim_id))
            ORDER BY CAST(updated_at AS TIMESTAMP) DESC
        ) AS rn
    FROM raw_source
    WHERE amount_usd > 0 AND claim_id IS NOT NULL
)

SELECT
    claim_id,
    tenant_id,
    amount_usd,
    claim_status,
    updated_at
FROM deduplicated
WHERE rn = 1
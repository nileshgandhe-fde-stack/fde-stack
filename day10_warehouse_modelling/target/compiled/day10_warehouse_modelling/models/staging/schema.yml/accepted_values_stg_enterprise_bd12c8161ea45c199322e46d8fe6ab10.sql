
    
    

with all_values as (

    select
        claim_status as value_field,
        count(*) as n_records

    from "fde_warehouse"."main"."stg_enterprise_claims"
    group by claim_status

)

select *
from all_values
where value_field not in (
    'PENDING','APPROVED','DENIED','ESCALATED'
)



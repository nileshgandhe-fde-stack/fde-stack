
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        claim_status as value_field,
        count(*) as n_records

    from "neondb"."public"."stg_enterprise_claims"
    group by claim_status

)

select *
from all_values
where value_field not in (
    'PENDING','APPROVED','DENIED','ESCALATED'
)



  
  
      
    ) dbt_internal_test
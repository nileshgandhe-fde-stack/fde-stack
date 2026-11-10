
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select amount_usd
from "fde_warehouse"."main"."raw_claims"
where amount_usd is null



  
  
      
    ) dbt_internal_test
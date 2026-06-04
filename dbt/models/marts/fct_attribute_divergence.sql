with divergence as (
    select * from {{ ref('int_system_attribute_divergence') }}
)

select
    sku,
    system,
    field,
    system_value,
    mor_value,
    abs_delta,
    pct_delta,
    case
        when field like '%weight%' and abs_delta > 0.5 then true
        when field like '%_in' and abs_delta > 0.5 then true
        else false
    end as flagged
from divergence

with fc as (
    select * from {{ ref('int_freight_class_by_system') }}
)

select
    sku,
    system,
    case_gross_weight_lb,
    case_length_in,
    case_width_in,
    case_height_in,
    case_cube_ft3,
    density_lb_per_ft3,
    freight_class
from fc

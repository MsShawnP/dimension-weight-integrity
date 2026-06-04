with mor as (
    select * from {{ ref('int_measurement_of_record') }}
)

select
    sku,
    product_name,
    mor_source,
    case_gross_weight_lb,
    case_length_in,
    case_width_in,
    case_height_in,
    unit_weight_lb,
    case_pack_qty,
    case_cube_ft3,
    density_lb_per_ft3,
    freight_class
from mor

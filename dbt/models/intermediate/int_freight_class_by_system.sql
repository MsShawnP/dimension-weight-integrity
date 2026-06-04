with erp as (
    select * from {{ ref('stg_netsuite_items') }}
),

wms as (
    select * from {{ ref('stg_wms_dimensions') }}
),

gdsn as (
    select * from {{ ref('stg_gdsn_published') }}
),

all_systems as (
    select sku, system, case_gross_weight_lb, case_length_in, case_width_in, case_height_in
    from erp
    union all
    select sku, system, case_gross_weight_lb, case_length_in, case_width_in, case_height_in
    from wms
    union all
    select sku, system, case_gross_weight_lb, case_length_in, case_width_in, case_height_in
    from gdsn
),

with_class as (
    select
        sku,
        system,
        case_gross_weight_lb,
        case_length_in,
        case_width_in,
        case_height_in,
        {{ cube_ft3('case_length_in', 'case_width_in', 'case_height_in') }} as case_cube_ft3,
        case_gross_weight_lb / nullif({{ cube_ft3('case_length_in', 'case_width_in', 'case_height_in') }}, 0)
            as density_lb_per_ft3,
        {{ density_to_nmfc_class(
            'case_gross_weight_lb / nullif(' ~ cube_ft3('case_length_in', 'case_width_in', 'case_height_in') ~ ', 0)'
        ) }} as freight_class
    from all_systems
    where case_length_in is not null
      and case_width_in is not null
      and case_height_in is not null
)

select * from with_class

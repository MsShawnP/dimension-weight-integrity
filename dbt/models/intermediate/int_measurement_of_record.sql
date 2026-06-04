with wms as (
    select * from {{ ref('stg_wms_dimensions') }}
),

measurement_of_record as (
    select
        sku,
        product_name,
        'wms' as mor_source,
        case_gross_weight_lb,
        case_length_in,
        case_width_in,
        case_height_in,
        unit_weight_lb,
        case_pack_qty,
        {{ cube_ft3('case_length_in', 'case_width_in', 'case_height_in') }} as case_cube_ft3,
        case_gross_weight_lb / nullif({{ cube_ft3('case_length_in', 'case_width_in', 'case_height_in') }}, 0)
            as density_lb_per_ft3,
        {{ density_to_nmfc_class(
            'case_gross_weight_lb / nullif(' ~ cube_ft3('case_length_in', 'case_width_in', 'case_height_in') ~ ', 0)'
        ) }} as freight_class
    from wms
)

select * from measurement_of_record

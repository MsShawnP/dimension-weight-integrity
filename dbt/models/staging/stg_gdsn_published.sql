with source as (
    select * from {{ source('raw', 'gdsn_published') }}
),

renamed as (
    select
        sku,
        product_name,
        'gdsn' as system,
        nullif(case_gross_weight_lb, '')::numeric as case_gross_weight_lb,
        nullif(case_length_in, '')::numeric as case_length_in,
        nullif(case_width_in, '')::numeric as case_width_in,
        nullif(case_height_in, '')::numeric as case_height_in,
        nullif(unit_weight_lb, '')::numeric as unit_weight_lb,
        nullif(case_pack_qty, '')::int as case_pack_qty
    from source
)

select * from renamed

with mor as (
    select * from {{ ref('int_measurement_of_record') }}
),

shopify as (
    select * from {{ ref('stg_shopify_products') }}
),

parcel_weights as (
    select
        mor.sku,
        mor.unit_weight_lb + 1.05 as dtc_parcel_gross_lb,
        shopify.ship_weight_lb as shopify_ship_weight_lb,
        coalesce(shopify.case_length_in, 6.0) as parcel_length_in,
        coalesce(shopify.case_width_in, 6.0) as parcel_width_in,
        coalesce(shopify.case_height_in, 6.0) as parcel_height_in,
        {{ dim_weight_lb(
            'coalesce(shopify.case_length_in, 6.0)',
            'coalesce(shopify.case_width_in, 6.0)',
            'coalesce(shopify.case_height_in, 6.0)',
            '139'
        ) }} as dim_weight_lb,
        {{ billable_weight_lb(
            'mor.unit_weight_lb + 1.05',
            dim_weight_lb(
                'coalesce(shopify.case_length_in, 6.0)',
                'coalesce(shopify.case_width_in, 6.0)',
                'coalesce(shopify.case_height_in, 6.0)',
                '139'
            )
        ) }} as billable_weight_lb
    from mor
    join shopify using (sku)
)

select * from parcel_weights

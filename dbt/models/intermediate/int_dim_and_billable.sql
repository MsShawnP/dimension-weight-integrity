with mor as (
    select * from {{ ref('int_measurement_of_record') }}
),

shopify as (
    select * from {{ ref('stg_shopify_products') }}
),

-- A DTC order ships ONE unit in a small parcel box, never the retail case.
-- DIM-weight the parcel from the per-unit box (dtc_parcel_box_in), NOT the
-- Shopify-published case dimensions: those describe the 12-count case and
-- would DIM-weight a single-jar parcel as if it were a full case, inflating
-- billable weight and the parcel-reweigh cost for the ~20% of SKUs whose
-- Shopify dims are populated.
parcel_weights as (
    select
        mor.sku,
        mor.unit_weight_lb + {{ var('packaging_offset_lb') }} as dtc_parcel_gross_lb,
        shopify.ship_weight_lb as shopify_ship_weight_lb,
        {{ var('dtc_parcel_box_in') }} as parcel_length_in,
        {{ var('dtc_parcel_box_in') }} as parcel_width_in,
        {{ var('dtc_parcel_box_in') }} as parcel_height_in,
        {{ dim_weight_lb(
            var('dtc_parcel_box_in'),
            var('dtc_parcel_box_in'),
            var('dtc_parcel_box_in'),
            var('dim_divisor')
        ) }} as dim_weight_lb,
        {{ billable_weight_lb(
            'mor.unit_weight_lb + ' ~ var('packaging_offset_lb'),
            dim_weight_lb(
                var('dtc_parcel_box_in'),
                var('dtc_parcel_box_in'),
                var('dtc_parcel_box_in'),
                var('dim_divisor')
            )
        ) }} as billable_weight_lb
    from mor
    join shopify using (sku)
)

select * from parcel_weights

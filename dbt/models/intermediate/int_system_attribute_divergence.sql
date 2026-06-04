with mor as (
    select * from {{ ref('int_measurement_of_record') }}
),

erp as (
    select * from {{ ref('stg_netsuite_items') }}
),

wms as (
    select * from {{ ref('stg_wms_dimensions') }}
),

gdsn as (
    select * from {{ ref('stg_gdsn_published') }}
),

shopify as (
    select * from {{ ref('stg_shopify_products') }}
),

-- Like-to-like: retail systems compare case_gross_weight_lb to case_gross_weight_lb
retail_divergence as (
    -- ERP weight divergence
    select
        erp.sku,
        'erp' as system,
        'case_gross_weight_lb' as field,
        erp.case_gross_weight_lb as system_value,
        mor.case_gross_weight_lb as mor_value,
        abs(erp.case_gross_weight_lb - mor.case_gross_weight_lb) as abs_delta,
        abs(erp.case_gross_weight_lb - mor.case_gross_weight_lb) / nullif(mor.case_gross_weight_lb, 0) as pct_delta
    from erp
    join mor using (sku)

    union all

    -- ERP dimension divergence (length)
    select
        erp.sku, 'erp', 'case_length_in',
        erp.case_length_in, mor.case_length_in,
        abs(erp.case_length_in - mor.case_length_in),
        abs(erp.case_length_in - mor.case_length_in) / nullif(mor.case_length_in, 0)
    from erp join mor using (sku)

    union all

    select
        erp.sku, 'erp', 'case_width_in',
        erp.case_width_in, mor.case_width_in,
        abs(erp.case_width_in - mor.case_width_in),
        abs(erp.case_width_in - mor.case_width_in) / nullif(mor.case_width_in, 0)
    from erp join mor using (sku)

    union all

    select
        erp.sku, 'erp', 'case_height_in',
        erp.case_height_in, mor.case_height_in,
        abs(erp.case_height_in - mor.case_height_in),
        abs(erp.case_height_in - mor.case_height_in) / nullif(mor.case_height_in, 0)
    from erp join mor using (sku)

    union all

    -- WMS divergence (should be ~0 since WMS = MoR)
    select
        wms.sku, 'wms', 'case_gross_weight_lb',
        wms.case_gross_weight_lb, mor.case_gross_weight_lb,
        abs(wms.case_gross_weight_lb - mor.case_gross_weight_lb),
        abs(wms.case_gross_weight_lb - mor.case_gross_weight_lb) / nullif(mor.case_gross_weight_lb, 0)
    from wms join mor using (sku)

    union all

    -- GDSN divergence
    select
        gdsn.sku, 'gdsn', 'case_gross_weight_lb',
        gdsn.case_gross_weight_lb, mor.case_gross_weight_lb,
        abs(gdsn.case_gross_weight_lb - mor.case_gross_weight_lb),
        abs(gdsn.case_gross_weight_lb - mor.case_gross_weight_lb) / nullif(mor.case_gross_weight_lb, 0)
    from gdsn join mor using (sku)

    union all

    select
        gdsn.sku, 'gdsn', 'case_length_in',
        gdsn.case_length_in, mor.case_length_in,
        abs(gdsn.case_length_in - mor.case_length_in),
        abs(gdsn.case_length_in - mor.case_length_in) / nullif(mor.case_length_in, 0)
    from gdsn join mor using (sku)

    union all

    select
        gdsn.sku, 'gdsn', 'case_width_in',
        gdsn.case_width_in, mor.case_width_in,
        abs(gdsn.case_width_in - mor.case_width_in),
        abs(gdsn.case_width_in - mor.case_width_in) / nullif(mor.case_width_in, 0)
    from gdsn join mor using (sku)

    union all

    select
        gdsn.sku, 'gdsn', 'case_height_in',
        gdsn.case_height_in, mor.case_height_in,
        abs(gdsn.case_height_in - mor.case_height_in),
        abs(gdsn.case_height_in - mor.case_height_in) / nullif(mor.case_height_in, 0)
    from gdsn join mor using (sku)
),

-- Like-to-like: DTC compares dtc_parcel_gross_lb (MoR) vs ship_weight_lb (Shopify)
dtc_divergence as (
    select
        shopify.sku,
        'shopify' as system,
        'ship_weight_lb' as field,
        shopify.ship_weight_lb as system_value,
        mor.unit_weight_lb + 1.05 as mor_value,  -- dtc_parcel_gross_lb = unit_net + packaging
        abs(shopify.ship_weight_lb - (mor.unit_weight_lb + 1.05)) as abs_delta,
        abs(shopify.ship_weight_lb - (mor.unit_weight_lb + 1.05)) / nullif(mor.unit_weight_lb + 1.05, 0) as pct_delta
    from shopify
    join mor using (sku)
)

select * from retail_divergence
union all
select * from dtc_divergence

with mor as (
    select * from {{ ref('int_measurement_of_record') }}
),

fc_by_system as (
    select * from {{ ref('int_freight_class_by_system') }}
),

billable as (
    select * from {{ ref('int_dim_and_billable') }}
),

gdsn_class as (
    select sku, freight_class as gdsn_freight_class, density_lb_per_ft3 as gdsn_density
    from fc_by_system
    where system = 'gdsn'
),

-- LTL reclass cost: class difference between GDSN-published and MoR
ltl_reclass as (
    select
        mor.sku,
        'ltl_reclass' as cost_driver,
        case
            when gdsn_class.gdsn_freight_class != mor.freight_class then
                -- Cost difference per cwt between the two classes, applied to case weight
                -- Uses rate table from config (loaded via dbt vars)
                (mor.case_gross_weight_lb / 100.0) * (
                    case gdsn_class.gdsn_freight_class
                        when 50 then 18.00 when 55 then 19.80 when 60 then 21.78
                        when 65 then 23.96 when 70 then 26.35 when 77.5 then 28.99
                        when 85 then 31.89 when 92.5 then 35.08 when 100 then 38.59
                        when 110 then 42.44 when 125 then 46.69 when 150 then 51.36
                        when 175 then 56.49 when 200 then 62.14 when 250 then 68.36
                        when 300 then 75.19 when 400 then 82.71 when 500 then 90.98
                    end
                    -
                    case mor.freight_class
                        when 50 then 18.00 when 55 then 19.80 when 60 then 21.78
                        when 65 then 23.96 when 70 then 26.35 when 77.5 then 28.99
                        when 85 then 31.89 when 92.5 then 35.08 when 100 then 38.59
                        when 110 then 42.44 when 125 then 46.69 when 150 then 51.36
                        when 175 then 56.49 when 200 then 62.14 when 250 then 68.36
                        when 300 then 75.19 when 400 then 82.71 when 500 then 90.98
                    end
                )
            else 0
        end as per_unit_delta,
        52 as annual_units,
        jsonb_build_object(
            'gdsn_class', gdsn_class.gdsn_freight_class,
            'mor_class', mor.freight_class,
            'gdsn_density', round(gdsn_class.gdsn_density::numeric, 2),
            'mor_density', round(mor.density_lb_per_ft3::numeric, 2),
            'case_weight_lb', mor.case_gross_weight_lb
        ) as basis
    from mor
    left join gdsn_class using (sku)
),

-- Parcel reweigh cost: difference between billable weight and Shopify weight
parcel_reweigh as (
    select
        billable.sku,
        'parcel_reweigh' as cost_driver,
        case
            when billable.billable_weight_lb > ceil(billable.shopify_ship_weight_lb) then
                -- Rate lookup for billable vs Shopify weight tier
                (case billable.billable_weight_lb::int
                    when 1 then 9.80 when 2 then 10.96 when 3 then 11.77
                    when 4 then 12.41 when 5 then 12.97 else 12.97
                end)
                -
                (case ceil(billable.shopify_ship_weight_lb)::int
                    when 1 then 9.80 when 2 then 10.96 when 3 then 11.77
                    when 4 then 12.41 when 5 then 12.97 else 12.97
                end)
            else 0
        end as per_unit_delta,
        200 as annual_units,
        jsonb_build_object(
            'billable_weight_lb', billable.billable_weight_lb,
            'shopify_weight_lb', billable.shopify_ship_weight_lb,
            'dim_weight_lb', round(billable.dim_weight_lb::numeric, 3),
            'dtc_parcel_gross_lb', round(billable.dtc_parcel_gross_lb::numeric, 2)
        ) as basis
    from billable
),

-- Compliance chargeback cost
compliance_cb as (
    select
        mor.sku,
        'compliance_cb' as cost_driver,
        case
            when gdsn_class.gdsn_freight_class is not null
                 and gdsn_class.gdsn_freight_class != mor.freight_class
            then 200.00
            else 0
        end as per_unit_delta,
        3 as annual_units,
        jsonb_build_object(
            'reason', 'dimension_mismatch',
            'gdsn_class', gdsn_class.gdsn_freight_class,
            'mor_class', mor.freight_class
        ) as basis
    from mor
    left join gdsn_class using (sku)
),

all_costs as (
    select sku, cost_driver, round(per_unit_delta::numeric, 2) as per_unit_delta,
           annual_units, round((per_unit_delta * annual_units)::numeric, 2) as annual_cost, basis
    from ltl_reclass
    union all
    select sku, cost_driver, round(per_unit_delta::numeric, 2),
           annual_units, round((per_unit_delta * annual_units)::numeric, 2), basis
    from parcel_reweigh
    union all
    select sku, cost_driver, round(per_unit_delta::numeric, 2),
           annual_units, round((per_unit_delta * annual_units)::numeric, 2), basis
    from compliance_cb
)

select * from all_costs

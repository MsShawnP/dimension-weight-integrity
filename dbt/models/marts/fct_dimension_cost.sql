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

ltl_reclass as (
    select
        mor.sku,
        'ltl_reclass' as cost_driver,
        case
            when gdsn_class.gdsn_freight_class != mor.freight_class then
                -- Floor at 0: a downward class shift triggers a carrier
                -- reweigh/back-bill, never a saving. No negative reclass cost.
                greatest(0, (mor.case_gross_weight_lb / 100.0) * (
                    {{ ltl_rate_lookup('gdsn_class.gdsn_freight_class') }}
                    -
                    {{ ltl_rate_lookup('mor.freight_class') }}
                ))
            else 0
        end as per_unit_delta,
        {{ var('annual_pallet_shipments_per_sku') }} as annual_units,
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

parcel_reweigh as (
    select
        billable.sku,
        'parcel_reweigh' as cost_driver,
        case
            when billable.billable_weight_lb > ceil(billable.shopify_ship_weight_lb) then
                {{ parcel_rate_lookup('billable.billable_weight_lb::int') }}
                -
                {{ parcel_rate_lookup('ceil(billable.shopify_ship_weight_lb)::int') }}
            else 0
        end as per_unit_delta,
        {{ var('annual_dtc_orders_per_sku') }} as annual_units,
        jsonb_build_object(
            'billable_weight_lb', billable.billable_weight_lb,
            'shopify_weight_lb', billable.shopify_ship_weight_lb,
            'dim_weight_lb', round(billable.dim_weight_lb::numeric, 3),
            'dtc_parcel_gross_lb', round(billable.dtc_parcel_gross_lb::numeric, 2)
        ) as basis
    from billable
),

compliance_cb as (
    select
        mor.sku,
        'compliance_cb' as cost_driver,
        case
            when gdsn_class.gdsn_freight_class is not null
                 and gdsn_class.gdsn_freight_class != mor.freight_class
            then {{ var('chargeback_per_event_cost') }}
            else 0
        end as per_unit_delta,
        -- affected_sku_pct: only ~40% of divergent SKUs actually incur
        -- chargebacks, so scale expected events (3 -> 1.2). Keeps the per-event
        -- cost at the cited $200 SQEP base rather than understating it.
        {{ var('annual_chargeback_events_per_sku') }} * {{ var('chargeback_affected_sku_pct') }} as annual_units,
        jsonb_build_object(
            'reason', 'dimension_mismatch',
            'gdsn_class', gdsn_class.gdsn_freight_class,
            'mor_class', mor.freight_class
        ) as basis
    from mor
    left join gdsn_class using (sku)
),

-- annual_cost rounds the per-unit delta to cents BEFORE annualizing so the
-- displayed "per_unit x annual_units = annual_cost" reconciles exactly.
all_costs as (
    select sku, cost_driver, round(per_unit_delta::numeric, 2) as per_unit_delta,
           annual_units, round((round(per_unit_delta::numeric, 2) * annual_units)::numeric, 2) as annual_cost, basis
    from ltl_reclass
    union all
    select sku, cost_driver, round(per_unit_delta::numeric, 2),
           annual_units, round((round(per_unit_delta::numeric, 2) * annual_units)::numeric, 2), basis
    from parcel_reweigh
    union all
    select sku, cost_driver, round(per_unit_delta::numeric, 2),
           annual_units, round((round(per_unit_delta::numeric, 2) * annual_units)::numeric, 2), basis
    from compliance_cb
)

select * from all_costs

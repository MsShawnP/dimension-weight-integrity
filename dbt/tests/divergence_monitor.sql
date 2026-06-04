-- Divergence monitor: warns when case_gross_weight_lb diverges beyond tolerance.
-- Severity: warn (not error) — expected to fire for ERP, GDSN, Shopify on divergent SKUs.
-- Must NOT fire for WMS (WMS = MoR by definition).
-- Config: drift_tolerance_lb = 0.5
{{ config(severity='warn') }}

select
    sku,
    system,
    field,
    system_value,
    mor_value,
    abs_delta
from {{ ref('fct_attribute_divergence') }}
where field = 'case_gross_weight_lb'
  and abs_delta > 0.5
  and system != 'wms'

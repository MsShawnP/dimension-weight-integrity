-- Unit tests for physical computation macros.
-- Run with: dbt test --select test_macros
-- Each CTE tests one macro invocation; the final query asserts all pass.

with test_cases as (

    -- cube_ft3 tests
    select
        'cube_ft3 hero SKU' as test_name,
        round(({{ cube_ft3('11.25', '8.5', '5.25') }})::numeric, 5) as actual,
        0.29053 as expected

    union all select
        'cube_ft3 unit cube (12×12×12)' as test_name,
        round(({{ cube_ft3('12.0', '12.0', '12.0') }})::numeric, 5) as actual,
        1.00000 as expected

    union all select
        'cube_ft3 small box (6×6×6)' as test_name,
        round(({{ cube_ft3('6.0', '6.0', '6.0') }})::numeric, 5) as actual,
        0.12500 as expected

    -- density_to_nmfc_class tests
    union all select
        'nmfc class 50 — hero SKU MoR (74.0)' as test_name,
        ({{ density_to_nmfc_class('74.0') }})::numeric as actual,
        50 as expected

    union all select
        'nmfc class 55 — GDSN published (37.98)' as test_name,
        ({{ density_to_nmfc_class('37.98') }})::numeric as actual,
        55 as expected

    union all select
        'nmfc class 50 — exact boundary (50.0)' as test_name,
        ({{ density_to_nmfc_class('50.0') }})::numeric as actual,
        50 as expected

    union all select
        'nmfc class 55 — just below boundary (49.99)' as test_name,
        ({{ density_to_nmfc_class('49.99') }})::numeric as actual,
        55 as expected

    union all select
        'nmfc class 85 — mid range (13.0)' as test_name,
        ({{ density_to_nmfc_class('13.0') }})::numeric as actual,
        85 as expected

    union all select
        'nmfc class 250 — low density (3.5)' as test_name,
        ({{ density_to_nmfc_class('3.5') }})::numeric as actual,
        250 as expected

    union all select
        'nmfc class 500 — lowest (0.5)' as test_name,
        ({{ density_to_nmfc_class('0.5') }})::numeric as actual,
        500 as expected

    -- dim_weight_lb tests (per-dimension ceiling before division)
    union all select
        'dim_weight_lb 6×6×6 / 139' as test_name,
        round(({{ dim_weight_lb('6.0', '6.0', '6.0', '139') }})::numeric, 3) as actual,
        round((216.0 / 139.0)::numeric, 3) as expected

    union all select
        'dim_weight_lb fractional dims 6.1×6.2×6.3 / 139' as test_name,
        round(({{ dim_weight_lb('6.1', '6.2', '6.3', '139') }})::numeric, 3) as actual,
        round((7.0 * 7.0 * 7.0 / 139.0)::numeric, 3) as expected

    union all select
        'dim_weight_lb hero parcel (6×6×6 jar box) / 139' as test_name,
        round(({{ dim_weight_lb('6.0', '6.0', '6.0', '139') }})::numeric, 3) as actual,
        round((216.0 / 139.0)::numeric, 3) as expected

    -- billable_weight_lb tests
    union all select
        'billable_weight_lb actual > dim (2.05 vs 1.554)' as test_name,
        ({{ billable_weight_lb('2.05', '1.554') }})::numeric as actual,
        3 as expected

    union all select
        'billable_weight_lb exact integer (3.0 vs 3.0)' as test_name,
        ({{ billable_weight_lb('3.0', '3.0') }})::numeric as actual,
        3 as expected

    union all select
        'billable_weight_lb dim > actual (1.0 vs 2.5)' as test_name,
        ({{ billable_weight_lb('1.0', '2.5') }})::numeric as actual,
        3 as expected

)

select test_name, actual, expected
from test_cases
where actual != expected

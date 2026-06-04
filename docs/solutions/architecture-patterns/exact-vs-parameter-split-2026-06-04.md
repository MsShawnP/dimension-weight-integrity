---
title: "Exact vs Parameter Split: Separating Physics from Business Assumptions"
date: 2026-06-04
category: architecture-patterns
module: dimension-weight-integrity
problem_type: architecture_pattern
component: database
severity: medium
related_components:
  - tooling
  - testing_framework
applies_when:
  - Building a data pipeline that produces dollar-denominated cost or impact claims
  - Multiple audiences will audit different layers (physics vs business assumptions)
  - The same codebase serves demo (industry benchmarks) and production (client-specific rates)
  - Cost analysis must survive review by supply-chain analysts, CFOs, and data engineers
tags:
  - exact-vs-parameter
  - dbt-vars
  - cost-analysis
  - auditability
  - credibility
  - physics-computation
  - cinderhaven
---

# Exact vs Parameter Split: Separating Physics from Business Assumptions

## Context

When building a data-driven cost analysis -- one that computes dollar losses from conflicting data across ERP, WMS, GDSN, and DTC systems -- the piece's credibility depends on whether a reader can audit the math. If physics formulas and business assumptions are tangled together in SQL queries, nobody can tell which numbers are derivable truths and which are calibratable guesses.

The Dimension & Weight Integrity project needed to answer "how much does inconsistent product dimension and weight data cost per year?" in a way that withstands scrutiny. The architecture that emerged cleanly separates computed physics from configurable business assumptions, making each independently auditable and adjustable.

This pattern was stated as a design principle upfront, but the code review (17 findings, all resolved) revealed that 4 SQL files had violated it by hard-coding business parameters directly in SQL. The extraction of those values into dbt vars was the review's most impactful correction -- evidence that the principle needs active enforcement, not just declaration. (session history)

## Guidance

### The two layers

**Exact layer (physics and standards):** Formulas derivable from first principles or published standards. These are computed, never stored as constants. Anyone with a textbook can verify them.

- Cubic volume: `length * width * height / 1728`
- Density: `weight / cubic_volume`
- NMFC freight class: density-to-class lookup table (NMFTA standard)
- DIM weight: `ceil(L) * ceil(W) * ceil(H) / divisor` (per-dimension ceiling, per carrier billing method)
- Billable weight: `ceil(max(actual_weight, dim_weight))`

**Parameter layer (business configuration):** Values that depend on negotiated rates, business volume, or operational estimates. Flagged with `# PARAM`, centralized in a single config file, sourced into the computation layer through a documented path.

- LTL rate table ($/cwt by NMFC class)
- Parcel rate table ($/shipment by weight tier)
- Annual volumes (shipments per SKU, DTC orders per SKU)
- Chargeback costs (per event)
- Tolerances (weight and dimension divergence thresholds)
- DIM divisor (139 -- industry standard but carrier-specific, so it is a parameter)
- Packaging offset (unit net weight to DTC parcel gross)

### The flow path for parameters

```
config/cost_params.yml          -- single source, PARAM-tagged, source-cited
    |
    v
dbt_project.yml vars:           -- dbt picks them up as project variables
    |
    v
SQL via {{ var('...') }}        -- models reference vars, never literals
    |
    v
dbt macros (rate_lookup.sql)    -- reusable lookup logic, parameterized
```

### Physics as dbt macros

Each physics formula lives in its own macro, documented with its source:

```sql
-- dbt/macros/dim_weight_lb.sql
{% macro dim_weight_lb(length_in, width_in, height_in, divisor) %}
    (ceil({{ length_in }}) * ceil({{ width_in }}) * ceil({{ height_in }}))
    / {{ divisor }}::numeric
{% endmacro %}
```

### Parameters as dbt vars with macro-based lookups

```sql
-- dbt/macros/rate_lookup.sql
{% macro ltl_rate_lookup(class_expr) %}
    case {{ class_expr }}
        {% for class_key, rate in var('ltl_rate_per_cwt').items() %}
        when {{ class_key }} then {{ rate }}
        {% endfor %}
    end
{% endmacro %}
```

The config file documents every value's source:

```yaml
# config/cost_params.yml
ltl:
  rate_per_cwt:  # PARAM -- $/cwt by NMFC freight class
    50: 18.00
    55: 19.80
    # Red Stag Fulfillment rate index, Jansson LLC

parcel:
  dim_divisor: 139  # PARAM -- FedEx/UPS domestic standard
  annual_dtc_orders_per_sku: 200  # PARAM -- estimated DTC orders/SKU
```

### E2E reconciliation tests verify the boundary

Tests independently recompute physics from raw inputs and compare to pipeline output:

```python
class TestPhysicalConstants:
    def test_cube_ft3(self, hero):
        mor = hero["hero_sku"]["measurement_of_record"]
        expected = (mor["case_length_in"] * mor["case_width_in"]
                    * mor["case_height_in"]) / 1728
        assert math.isclose(mor["case_cube_ft3"], expected, rel_tol=1e-3)
```

## Why This Matters

**Auditability.** A reviewer can check the physics layer against published standards (NMFTA density tables, carrier DIM-weight formulas) without needing access to proprietary rate cards.

**Calibratability.** When a real client engagement begins, only `config/cost_params.yml` gets updated with actual negotiated rates and real shipment volumes. The pipeline reruns without touching SQL or macros.

**Credibility compounding.** The code review found 4 SQL files where this boundary had leaked -- rate table values embedded in CASE expressions, annual volume literals in SELECT clauses. Each leak was individually small, but collectively they meant an auditor could not tell which numbers were physics and which were assumptions. Extracting them restored the property the entire analysis depends on. (session history)

**Test architecture.** The split enables two independent test strategies: (1) E2E reconciliation tests that recompute physics from raw inputs; (2) parameter-presence tests that verify rate tables and config values are populated. Neither strategy works if the two layers are mixed.

## When to Apply

- **The analysis makes a cost or impact claim.** Any time code produces a dollar figure or risk score used for decisions, the inputs need to be auditable.
- **Multiple audiences will read the output.** A supply-chain analyst checks the physics. A CFO checks the dollar impact. A data engineer checks the pipeline.
- **The same codebase serves demo and production.** Demo uses industry-benchmarked parameters. Production uses client-specific parameters. Scattered parameters mean hunting through every model to switch.
- **You need to defend the work in a review.** "Show me where the $X number comes from" is the first question. With the split, the answer is always: "Physics are in `dbt/macros/`, derivable from standards. Rates are in `config/cost_params.yml`, sourced from [citation]. The pipeline multiplies one by the other."

Does **not** apply to: pure CRUD applications, throwaway prototypes, or systems where all values come from a single authoritative source.

## Examples

### Before: parameters hard-coded in SQL

```sql
-- fct_dimension_cost.sql (BEFORE)
parcel_reweigh as (
    select sku, 'parcel_reweigh' as cost_driver,
        case billable.billable_weight_lb::int
            when 1 then 9.80    -- hard-coded rate
            when 2 then 10.96   -- hard-coded rate
            when 3 then 11.77   -- hard-coded rate
            else 12.97          -- hard-coded fallback
        end as per_unit_delta,
        200 as annual_units,    -- hard-coded volume
    from billable
)
```

An auditor cannot distinguish a physics constant from a business assumption. Changing any parameter requires editing SQL.

### After: parameters extracted to dbt vars

```sql
-- fct_dimension_cost.sql (AFTER)
parcel_reweigh as (
    select sku, 'parcel_reweigh' as cost_driver,
        {{ parcel_rate_lookup('billable.billable_weight_lb::int') }}
        as per_unit_delta,
        {{ var('annual_dtc_orders_per_sku') }} as annual_units,
    from billable
)
```

The `parcel_rate_lookup` macro iterates over `var('parcel_rate_per_lb')`, which flows from `dbt_project.yml`, which mirrors `config/cost_params.yml`. Defined once, labeled, and source-cited.

### What didn't work during implementation (session history)

1. **dbt test assertions wrong on 3 density/class boundaries.** The density-to-NMFC-class macro was correct, but test assertions used wrong expected values (e.g., density 13.0 expected class 85, macro correctly returns 77.5 per NMFTA table). Tests had never been executed against a real database.
2. **`lookupRate` fallback in frontend domain.ts was wrong.** Weight above the largest rate-table bracket was silently clamped to the min bracket via `Math.min(key, 5)`, returning an incorrect low rate for heavy parcels. Fixed to return 0 with a clear signal.
3. **Vacuous test in test_export.py** compared `expected_keys == expected_keys` (always true). Fixed to actually read `hero.json` and compare its top-level keys.
4. **`if True` branch in export script** left a class-mismatch counter always counting all SKUs rather than only those with nonzero `ltl_reclass` cost.

## Related

- DECISIONS.md entry "Exact vs parameter split as credibility core" (2026-06-04)
- DECISIONS.md entry "All business parameters sourced from dbt vars" (2026-06-04)
- `config/cost_params.yml` — the parameter source file with citations
- `dbt/macros/rate_lookup.sql` — the macro that bridges config to SQL
- `tests/test_e2e_reconciliation.py` — E2E tests that verify the physics boundary

---
title: "Cost Driver Unit Mismatch: A $/Case Delta Multiplied by a Pallet Count"
date: 2026-07-28
category: logic-errors
module: dimension-weight-integrity
problem_type: logic_error
component: database
severity: critical
symptoms:
  - "Published LTL freight cost was ~200x too low ($20.28/yr for a SKU shipping $500k of product)"
  - "per_unit_delta and annual_units were in different units with nothing asserting they matched"
  - "Portfolio headline read $17,533 when the same inputs support $208,311"
  - "Full test suite passed green while the number was wrong"
root_cause: logic_error
resolution_type: code_fix
related_components:
  - testing_framework
  - documentation
tags:
  - unit-mismatch
  - cost-model
  - ltl-freight
  - hundredweight
  - dbt
  - dimensional-analysis
  - cancellation
  - review-findings
  - cinderhaven
---

# Cost Driver Unit Mismatch: A $/Case Delta Multiplied by a Pallet Count

## Problem

`fct_dimension_cost.sql` computed the LTL freight reclassification driver as a
per-**case** dollar delta and then multiplied it by a count of annual pallet
**shipments**. The two factors were in different units. The published cost for
the hero SKU was $20.28/yr against a true figure of $4,231.89/yr, and the
portfolio headline on a live client-facing site read $17,533 instead of
$208,311.

## Symptoms

- Hero LTL cost of $20.28/yr for a SKU moving roughly $500,000 of product
  annually — implausible on its face, but nothing flagged it
- `per_unit_delta` (dollars per case) and `annual_units` (pallet shipments)
  declared ~20 lines apart in the same CTE, neither naming its unit
- The entire magnitude of the driver rested on `annual_pallet_shipments_per_sku`,
  an unsourced parameter shipped at `52` while the build spec illustrated `520`
- 57 Python and 41 frontend tests passed. The frontend suite asserted the wrong
  number as a literal (`$20.28`, `$654.28`) against real pipeline output, so it
  actively defended the defect

## What Didn't Work

**Repricing the delta onto a pallet weight.** The finding that surfaced this
defect diagnosed it as a *basis* error and prescribed the fix: reprice the rate
delta onto a full pallet (40 cases × 21.50 lb = 860 lb = 8.60 cwt, Δ
$15.48/pallet), which requires a `ti`/`hi`/`cases_per_pallet` field that exists
nowhere in the schema. The finding explicitly said "that field has to be
generated first."

This is wrong, and following it would have added a physical field the model does
not need while double-counting the pallet term. Writing out the units shows why:

```
(cases_per_pallet × case_lb/100) × rate_delta × pallets_per_year
  == (case_lb/100) × rate_delta × (cases_per_pallet × pallets_per_year)
  == (case_lb/100) × rate_delta × annual_cases
```

`cases_per_pallet` **cancels**. LTL is billed per hundredweight, so a
reclassification penalty falls on tonnage shipped, not on how that tonnage is
stacked. Ship the same annual volume on 40-case or 128-case pallets and the
class-delta cost is identical. `per_unit_delta` was therefore already correct;
only the multiplier was wrong.

**Choosing between 52 and 520 pallets/yr.** The follow-up question — "config
ships 52, the spec illustrates 520, which is right?" — was the wrong axis. Both
are asserted pallet counts with no source. Their 10x spread compounded with the
basis question into a ~400x range on the headline, which is the tell that the
parameter itself was the problem, not its value.

**Two other findings in the same list also failed verification**, each refuted
in under two minutes by computing the claim directly:

| Claim | Reality |
|---|---|
| "All four committed CSVs fail UTF-8 decode, breaking any Linux checkout" | `data/generated/` is gitignored and was never committed; `git log -- data/generated/` is empty. A fresh clone has no CSVs at all |
| "Status pills should use HK-5 text on HK-35" | Measures **3.03:1** — worse than the 4.02:1 white it would replace |

## Solution

Leave `per_unit_delta` and all physics untouched. Replace only the multiplier
with an annual **case** count, derived rather than asserted.

Before:

```sql
        end as per_unit_delta,
        {{ var('annual_pallet_shipments_per_sku') }} as annual_units,
```

After:

```sql
        end as per_unit_delta,
        -- per_unit_delta above is $/CASE (case cwt x rate delta), so the
        -- multiplier must be an annual CASE count. It was previously a count
        -- of pallet SHIPMENTS (52/yr) -- a unit mismatch, and one that left
        -- the size of this whole driver resting on an unsourced pallet count.
        -- LTL bills by hundredweight, so how cases stack is irrelevant:
        -- cases_per_pallet cancels between the two factors.
        round(
            {{ var('annual_wholesale_revenue_per_sku') }}
            / {{ var('wholesale_price_per_unit') }}
            / nullif(mor.case_pack_qty, 0)
        ) as annual_units,
```

The volume is now derived from figures the dataset already discloses, which
collapses two unsourced parameters into one sourced price:

```yaml
# config/cost_params.yml
annual_wholesale_revenue_per_sku: 500000.00  # DERIVED — $25M / 50 SKUs (CINDERHAVEN_CANONICAL.md)
wholesale_price_per_unit: 3.84  # PARAM — catalog mean MSRP $7.67 x blended non-DTC wholesale multiplier 0.5000
```

`case_pack_qty` is per-SKU and already carried in the measurement of record, so
SKUs packed 24-to-a-case correctly yield half the annual cases of 12-packs at
the same revenue.

Results after rebuilding marts and JSON offline:

| | Before | After |
|---|---|---|
| Hero LTL | $0.39/case × 52 pallets = $20.28 | $0.39/case × 10,851 cases = **$4,231.89** |
| Hero total | $654.28 | **$4,865.89** |
| Portfolio | $17,533.48 | **$208,310.87** |

## Why This Works

The carrier's billing basis decides the unit. LTL tariffs quote dollars per
hundredweight, so the only quantity that matters is weight moved per year.
Expressing that as `(lb per case / 100) × annual cases` is dimensionally
identical to `(lb per pallet / 100) × annual pallets` — the packing factor is
a change of variable, not an input. Introducing `ti`/`hi` would have added a
term that must cancel, creating a new opportunity to get it wrong.

Deriving the volume also removes the failure mode that made the defect
invisible. A free-floating `annual_pallet_shipments_per_sku` has no wrong value
— any number is defensible when nothing anchors it — so no test or reviewer
could call `52` incorrect. `annual_cases = revenue / price / case_pack` is
falsifiable: each input traces to a published figure, and a wrong result means
a wrong input, not a wrong opinion.

## Prevention

**State both units adjacent to each other.** A per-unit delta and its annual
multiplier must be in the same unit, and that unit is dictated by how the
counterparty bills (per cwt, per shipment, per event). The defect survived
because the two factors sat 20 lines apart and neither named its unit.

**Assert the unit contract in a test, not the output value.** Freezing
`$20.28` is what let this persist — the frontend suite asserted the wrong
number as a literal against real pipeline output, so it defended the bug. The
replacement pins the relationship instead:

```python
def test_ltl_annual_units_is_a_case_count_not_a_pallet_count(self, hero, cost_params):
    ltl = hero["cost"]["ltl_reclass"]
    cfg = cost_params["ltl"]
    expected = round(
        cfg["annual_wholesale_revenue_per_sku"]
        / cfg["wholesale_price_per_unit"]
        / ltl["basis"]["case_pack_qty"]
    )
    assert ltl["annual_units"] == expected
    # A weekly-pallet count is ~2 orders of magnitude too small for a
    # $500k/yr SKU's case volume.
    assert ltl["annual_units"] > 1000
```

**Bind published prose to the data.** `tests/test_readme_figures.py` now parses
the README's dollar figures back out and reconciles them against the shipped
JSON, including a guard that no driver is priced `× N pallets/yr`. Sabotaging
three figures fails it. See [Exact vs Parameter
Split](../architecture-patterns/exact-vs-parameter-split-2026-06-04.md) for the
related rule that physics is computed and only business assumptions are config.

**Verify a finding's diagnosis before implementing its fix.** Three of the
findings in this one fix list were wrong — a wrong prescription, a false
premise, and a fix that made the metric worse. Each was refuted by computing
the asserted quantity directly: the algebra, `git ls-files`, a WCAG ratio.
Findings are plausible and specific, which is exactly what makes them
persuasive enough to implement unchecked. Confirm the problem is real *and*
that the proposed fix beats the status quo. (auto memory [claude]: this project
already carried a rule to verify published figures against source data rather
than by reading code — the same discipline applied one level up, to the
findings themselves.)

**Sanity-check magnitude against a known anchor.** $20.28/yr of freight
exposure for a SKU moving ~$500,000 of product should have read as wrong
immediately. A one-line plausibility comparison against revenue would have
caught this without any of the unit analysis.

## Related Issues

- [Exact vs Parameter Split](../architecture-patterns/exact-vs-parameter-split-2026-06-04.md)
  — the physics-vs-config boundary this fix operates inside; the unit mismatch
  lived on the parameter side, which is why physics tests never caught it
- `DECISIONS.md` (2026-07-28) — three durable rules from this fix: verify
  findings before implementing, derive annual volumes from disclosed figures,
  check the billing unit before repricing a driver
- `FAILURES.md` (2026-07-28) — the two failure entries covering the wrong
  prescription and the two unverified claims
- `PLAN.md` — the original (incorrect) diagnosis is preserved next to the
  correction, since it nearly drove an unnecessary schema change

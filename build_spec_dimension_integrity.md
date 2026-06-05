# Build Spec — Dimension & Weight Integrity Piece (for Claude Code planning)

**Supersedes the brief for build purposes.** The brief (`portfolio_project_brief_dimension_integrity.md`) holds the *why* (narrative, positioning, audience). This doc holds the *how*: schemas, the cost engine, the dbt DAG, orchestration, the front-end data contract, and acceptance tests. Where the two disagree on a number, this doc wins.

**Substrate:** Full Cinderhaven Data Platform — Postgres + dbt + Dagster. Build inside the existing platform repo conventions. This piece **owns the physical-attribute fields** (`unit_*_weight`, `case_gross_weight`, `case_cube`, `length/width/height`, `ti`, `hi`); Product Data Health Audit owns structural completeness. Do not let the two models both write the dimension fields.

---

## 0. What's exact vs. what's a parameter

Be honest about this split in code and comments — it's the credibility core.

- **Exact (hard-coded, unit-tested):** cube math, density math, the density→NMFC class table, DIM-weight formula, billable-weight rule (greater-of, round up), and all reconciliation invariants. These are physics/standard tables and must be *computed*, never asserted.
- **Parameter (config, calibrate later, flagged `# PARAM`):** LTL $/cwt rate table, parcel $/lb rate table, chargeback $/event, annual pallet-shipment count, annual DTC order volume (← from DTC Channel Intelligence dataset), DIM divisor (carrier-specific), drift tolerance.

Put all parameters in one `config/cost_params.yml`. Nothing magic-numbered in model logic.

---

## 1. Architecture & data flow

```
seeds + generate_dimension_mess.py   (synthetic source extracts, one per system)
        │  (load to raw schema)
        ▼
raw.*  ──▶ dbt staging (stg_*)  ──▶ dbt intermediate (int_*)  ──▶ dbt marts (fct_*/dim_*)
                                          │                              │
                                  density→class macro,            governed master +
                                  dim-weight macro,               cost facts
                                  divergence unpivot
        │
        ▼
Dagster: asset graph  generate → load_raw → dbt build → export_frontend_json
        │
        ▼
frontend/  reads static  public/data/hero.json  (no live DB at runtime)
```

Runtime principle: the deployed front-end consumes a **static JSON exported by a Dagster asset**. The deployed piece never talks to Postgres. dbt/Python computes everything; the client only presents and runs the one live "paradox toggle" using rate tables shipped inside the JSON.

---

## 2. Hero SKU — the worked example (the anchor; everything must reconcile to this)

**`CH-MAR-16` — Cinderhaven Spicy Marinara, 16 oz glass jar, 12-count case.**

### 2.1 Measurement of Record (truth; promoted from the 3PL dock re-scan)

| Field | Value |
|---|---|
| `unit_net_weight_lb` | 1.00 |
| `unit_gross_weight_lb` | 1.69 (jar + lid + label + contents) |
| `dtc_parcel_gross_lb` | 2.05 (1 jar + mailer box + dunnage) |
| `dtc_box_dims_in` | 6 × 6 × 6 |
| `case_gross_weight_lb` | 21.50 |
| `case_dims_in (L×W×H)` | 11.25 × 8.50 × 5.25 |
| `case_cube_ft3` | 0.29053  (= 11.25·8.5·5.25 / 1728) |
| `case_density_lb_ft3` | **74.00** (= 21.50 / 0.29053) |
| `freight_class` | **50** (density ≥ 50 → class 50) |
| `ti` / `hi` | 8 / 5 → 40 cases/pallet |

### 2.2 What each system actually stores (the divergence)

| System | case_gross_lb | case dims (L×W×H) | density | class | other |
|---|---|---|---|---|---|
| **NetSuite ERP** | 20.00 (est. at setup) | 11 × 8 × 5 | 78.6 | 50 | `unit_weight_lb`=1.00 → **net entered in a gross field** (unit/case confusion); ti/hi = 8/6 (wrong hi) |
| **3PL / WMS** | 21.50 ✔ | 11.25 × 8.5 × 5.25 ✔ | 74.0 | 50 | dock parcel scan = 2.05 ✔ — **this system holds truth but never syncs back**; promote to MoR |
| **IX-ONE / GDSN (published)** | 22.00 | 13 × 11 × 7 (safe outer/overpack) | 37.98 | **55** | broadcast to channel; published ≠ physical → DC pallet/cube audit flag |
| **Shopify / DTC** | — | none stored | — | — | `ship_weight_lb`=1.00 → **net entered**, excludes glass+box; true parcel 2.05 |

The reveal for the "pick the true number" interaction: **none of ERP / GDSN / Shopify equals the MoR; only WMS does** — and WMS is the one system whose number never propagates.

### 2.3 The three cost drivers, computed

**(A) LTL freight reclass (retail).** Shipment basis = 1 pallet = 40 × 21.50 = 860 lb = 8.60 cwt.
Rate table `# PARAM`: class 50 = \$18.00/cwt, class 55 = \$19.80/cwt.
- True (class 50): 8.60 × 18.00 = **\$154.80 / pallet**
- Published-driven (class 55): 8.60 × 19.80 = **\$170.28 / pallet**
- **Δ = \$15.48 / pallet** → × `annual_pallets` `# PARAM` (e.g. 520) = **\$8,049.60 / yr**

**(B) Parcel reweigh back-bill (DTC).** Carrier bills the greater of actual and DIM weight, rounded up to the next whole lb.
DIM `# PARAM divisor = 139`: 6·6·6 / 139 = 1.554 lb. Actual 2.05 > DIM 1.554 → bill on 2.05 → **billable 3 lb**.
Parcel rate table `# PARAM`: 1 lb = \$8.50, 2 lb = \$9.75, 3 lb = \$11.00.
- Expected at Shopify weight (1 lb): \$8.50
- Carrier bill (3 lb): \$11.00
- **Leak = \$2.50 / order** → × `annual_dtc_orders[CH-MAR-16]` `# PARAM` (← DTC Channel Intelligence) = e.g. 6,000 → **\$15,000 / yr**
- (DIM is non-binding for this dense SKU; engine must still compute it — for a bulky-light SKU DIM would dominate. This is why the formula is `max`, not a fixed pick.)

**(C) Compliance chargeback attribution (retail).** Published dims/TiHi ≠ physical → retailer DC flags.
- `chargeback_per_event` `# PARAM` (e.g. \$250 flat, retailer-specific)
- `events_per_year` = attributed subset of Cinderhaven's 864 chargebacks coded to dimension/pallet-config `# PARAM` (e.g. 14% → ~121) — **must be added to the dataset and reconciled against the ~$3.5M/yr all-in trade spend (10.8% of scan revenue, trailing 52 weeks)**. Illustrative only — base 864 is canonical; 14% attribution and $250/event are UNCALIBRATED placeholders, calibrate at build. Not canonical figures.
- 121 × \$250 = **\$30,250 / yr** (illustrative — see note above)

All annual totals are placeholders until params are calibrated; the **per-unit math (Δ\$15.48/pallet, \$2.50/order) and the physical math must reconcile exactly** to §2.1–2.2.

### 2.4 Scaling to the 90-SKU master

`generate_dimension_mess.py` applies the same divergence *rules* (not the same numbers) to all 90 SKUs from a seeded RNG so it's deterministic and reproducible:
- ERP: weight biased low 3–8%, dims rounded to nearest inch, random ~20% have unit/case confusion.
- WMS: truth ± small scan noise (≤1%); always the MoR source.
- GDSN: dims inflated to a "safe outer box" (+10–25% per axis on a random subset), weight rounded up to nearest 0.5–1 lb; ti/hi sometimes off by one.
- Shopify: weight = net (unit_net) for a large subset (the systematic under-weight), dims null ~80%.

---

## 3. Data model (Postgres / dbt)

### 3.1 Raw (loaded from generated extracts — preserve per-system column quirks)

```sql
-- raw.netsuite_items
sku text, description text, unit_weight_lb numeric, case_weight_lb numeric,
case_l_in numeric, case_w_in numeric, case_h_in numeric, ti int, hi int, extracted_at timestamptz

-- raw.wms_dimensions
sku text, case_weight_lb numeric, length_in numeric, width_in numeric, height_in numeric,
ti int, hi int, parcel_weight_lb numeric, scanned_at timestamptz

-- raw.gdsn_published   (note GTIN present here, IX-ONE/SPINS origin)
sku text, gtin text, pub_case_weight_lb numeric, pub_l_in numeric, pub_w_in numeric,
pub_h_in numeric, pub_ti int, pub_hi int, published_at timestamptz

-- raw.shopify_products   (dims usually null)
sku text, variant_id text, ship_weight_lb numeric,
box_l_in numeric, box_w_in numeric, box_h_in numeric, updated_at timestamptz

-- reuse existing Cinderhaven tables; add/confirm a reason_code on chargebacks
-- raw.chargebacks (existing) : ..., reason_code text   -- subset coded 'DIM_PALLET'
-- raw.ltl_shipments  : shipment_id, ship_date, retailer, pallet_count, origin_zip, dest_zip
-- raw.dtc_orders     : order_id, sku, order_date, qty, ship_zip   -- volume must match DTC piece
```

### 3.2 Governed master (this piece owns these fields)

```sql
-- dim_product_measurement_of_record
sku text primary key,
unit_net_weight_lb numeric, unit_gross_weight_lb numeric,
dtc_parcel_gross_lb numeric, dtc_box_l_in numeric, dtc_box_w_in numeric, dtc_box_h_in numeric,
case_gross_weight_lb numeric, length_in numeric, width_in numeric, height_in numeric,
case_cube_ft3 numeric, case_density_lb_ft3 numeric, freight_class numeric,
ti int, hi int, cases_per_pallet int,
mor_source text default 'WMS', measured_at timestamptz
```

### 3.3 Marts (cost + divergence outputs the front-end reads)

```sql
-- fct_attribute_divergence   (long/tidy: one row per sku × system × field)
sku, system, field, system_value numeric, mor_value numeric,
abs_delta numeric, pct_delta numeric, flagged boolean   -- flagged = beyond tolerance

-- fct_freight_class_by_system
sku, system, density_lb_ft3 numeric, freight_class numeric

-- fct_dimension_cost   (one row per sku × driver)
sku, driver text,            -- 'ltl_reclass' | 'parcel_reweigh' | 'compliance_cb'
per_unit_delta numeric,      -- $/pallet or $/order or $/event
annual_units numeric,        -- pallets, orders, or events  (PARAM-sourced)
annual_cost numeric,
basis jsonb                  -- the inputs used, for traceability

-- fct_governed_product_master  (the merged "after" everything inherits)
```

---

## 4. dbt layer

### 4.1 Macros (the exact math lives here, unit-tested)

```
density_to_nmfc_class(density)   -- the full standard density band table, §App A
cube_ft3(l_in, w_in, h_in)       -- (l*w*h)/1728
dim_weight_lb(l, w, h, divisor)  -- (l*w*h)/divisor
billable_weight_lb(actual, dim)  -- ceil(greatest(actual, dim))
```

### 4.2 Model DAG

```
staging/      stg_netsuite_items, stg_wms_dimensions, stg_gdsn_published, stg_shopify_products
              (cast types, standardize column names, normalize units → lb / in)
intermediate/ int_measurement_of_record   -- promote WMS, compute cube/density/class via macros
              int_system_attribute_divergence -- unpivot each system vs MoR (gross-to-gross!)
              int_freight_class_by_system     -- density→class per system's stored dims
              int_dim_and_billable            -- parcel DIM + billable per SKU
marts/        fct_governed_product_master, fct_attribute_divergence,
              fct_freight_class_by_system, fct_dimension_cost
```

**Divergence comparison rule (critical):** compare like to like. Retail = case-gross vs case-gross; DTC = `dtc_parcel_gross_lb` (MoR) vs Shopify `ship_weight_lb`. **Never compare gross to net** — Shopify's net *should* differ from a gross field; the finding is that net was entered where gross belongs.

### 4.3 Tests / contracts

- `unique` + `not_null` on `dim_product_measurement_of_record.sku`.
- `accepted_range`: weights > 0, density > 0, freight_class in the valid set.
- Contract on `fct_dimension_cost` and the governed master (enforce column names/types).
- **Divergence monitor** (the showcase test): a custom singular test or `dbt_utils.expression_is_true` that **warns** when `abs_delta` for a gross-weight field exceeds `drift_tolerance_lb` `# PARAM` (e.g. 0.25). Severity `warn`, not error — it's a monitor, not a gate. This is what "policed continuously" means in the narrative.
- Macro unit tests (dbt unit tests): `density_to_nmfc_class(74.0)=50`, `(37.98)=55`, `(13.0)=85`; `dim_weight(6,6,6,139)≈1.554`; `billable_weight(2.05,1.554)=3`.

---

## 5. Dagster orchestration

Assets:
1. `generate_source_extracts` → writes 4 CSV/XLSX to `data/generated/` (seeded RNG).
2. `load_raw` → loads generated files into `raw.*`.
3. `dbt_build` → `dbt build` (models + tests).
4. `export_frontend_json` → queries marts, writes `frontend/public/data/hero.json` (§6 shape) and a full `all_skus.json`.

Schedule: on-demand for build; a daily schedule is fine for the demo to make "infrastructure not a spreadsheet" literal. Asset checks mirror the dbt divergence-monitor result so a drift shows up in the Dagster UI.

---

## 6. Front-end data contract

Front-end is presentation + one live toggle. **All dollars come from the JSON.** Ship the rate tables inside the JSON so the paradox toggle can recompute deltas client-side without a server.

```json
{
  "hero_sku": {
    "sku": "CH-MAR-16",
    "name": "Cinderhaven Spicy Marinara, 16oz, 12ct case",
    "measurement_of_record": { "case_gross_lb": 21.5, "dims_in": [11.25,8.5,5.25],
      "cube_ft3": 0.29053, "density": 74.0, "freight_class": 50,
      "dtc_parcel_lb": 2.05, "ti": 8, "hi": 5 },
    "systems": [
      { "system":"NetSuite ERP", "case_gross_lb":20.0, "dims_in":[11,8,5],
        "density":78.6, "freight_class":50, "note":"net entered in gross field; hi wrong" },
      { "system":"3PL / WMS", "case_gross_lb":21.5, "dims_in":[11.25,8.5,5.25],
        "density":74.0, "freight_class":50, "is_truth":true },
      { "system":"IX-ONE / GDSN", "case_gross_lb":22.0, "dims_in":[13,11,7],
        "density":37.98, "freight_class":55, "note":"safe-outer-box; broadcast to channel" },
      { "system":"Shopify / DTC", "ship_weight_lb":1.0, "dims_in":null,
        "note":"net weight; carrier reweighs to 2.05" }
    ]
  },
  "cost": {
    "ltl_reclass":   { "per_pallet_delta":15.48, "annual_pallets":520, "annual":8049.60 },
    "parcel_reweigh":{ "per_order_leak":2.50, "annual_orders":6000, "annual":15000.0 },
    "compliance_cb": { "per_event":250, "events":65, "annual":16250.0 }
  },
  "rate_tables": {
    "ltl_per_cwt": { "50":18.0, "55":19.8 },
    "parcel_per_lb": { "1":8.5, "2":9.75, "3":11.0 },
    "dim_divisor": 139
  },
  "paradox": {
    "ops_fix": { "action":"raise GDSN dims to safe outer box",
      "retail_effect":"class 50→55, +$15.48/pallet", "dtc_effect":"none directly",
      "note":"density falls, class rises across all distributors" },
    "dtc_fix": { "action":"lower Shopify weight to net",
      "retail_effect":"none directly", "dtc_effect":"carrier reweigh back-bill on every order" }
  }
}
```

Views:
- **V1 — Four-Weights panel:** the four systems side by side; user picks the "true" one; reveal that only WMS matches MoR. State-driven (a clean operational-audit-portal look, not a D3 scroll — per review note). Stack/framework chosen at planning; keep it a single deployable static site.
- **V2 — Two-directional bleed + Localization Paradox toggle:** show the retail path and DTC path; a toggle applies "ops fix" or "dtc fix" and recomputes the opposite-channel damage live from `rate_tables`. The lock: there is no toggle state where both channels are clean — only the governed MoR clears both.

---

## 7. Acceptance criteria (definition of done)

1. `dbt build` passes; macro unit tests green; divergence monitor emits `warn` for ERP/GDSN/Shopify on the hero SKU and not for WMS.
2. Reconciliation invariants hold exactly: cube 0.29053, density 74.0, class 50 for MoR; GDSN density 37.98 → class 55; LTL Δ = \$15.48/pallet; parcel billable = 3 lb, leak = \$2.50/order.
3. `fct_dimension_cost` rows for all three drivers, `annual_cost = per_unit_delta × annual_units`, with `basis` populated.
4. Exactly one system (WMS) equals the MoR in `fct_attribute_divergence` for the hero SKU; DTC comparison is parcel-gross vs ship-weight (not gross vs net).
5. Dagster `export_frontend_json` produces `hero.json` matching §6; front-end renders both views offline from it; paradox toggle is live and never reaches an all-clean state.
6. All `# PARAM` values resolved in `config/cost_params.yml`; none magic-numbered in models.

---

## 8. Repo layout

```
dimension-integrity/
  config/cost_params.yml
  data_gen/generate_dimension_mess.py
  dbt/
    macros/{density_to_nmfc_class.sql, cube_ft3.sql, dim_weight.sql, billable_weight.sql}
    models/staging/...  models/intermediate/...  models/marts/...
    tests/  unit_tests/
  dagster/assets.py
  frontend/  (static site; public/data/hero.json, all_skus.json)
  README.md
```

---

## 9. Params to lock before/at build (carried from open items)

- `annual_dtc_orders` per SKU — **pull from DTC Channel Intelligence dataset; do not invent a second DTC profile.**
- `annual_pallets`, `chargeback_per_event`, `events_per_year` (dimension-coded subset of 864 chargebacks) — set in `cost_params.yml`, reconcile against the ~$3.5M/yr all-in trade / 864-chargeback canon.
- Calibrate the LTL `$/cwt` and parcel `$/lb` tables to plausible current rates (these are modeled stand-ins).
- Confirm hero-SKU final specs (above are defensible working values; adjust once, then lock — every number downstream keys off them).

---

## Appendix A — Density → NMFC class table (exact; the macro implements this)

Standard density-based class guide (lb/ft³ → class). NMFC is technically commodity-specific; density classification is the standard modeled fallback — note this in the macro docstring.

| Density (lb/ft³) | Class | | Density | Class |
|---|---|---|---|---|
| ≥ 50 | 50 | | 10.5–12 | 92.5 |
| 35–50 | 55 | | 9–10.5 | 100 |
| 30–35 | 60 | | 8–9 | 110 |
| 22.5–30 | 65 | | 7–8 | 125 |
| 15–22.5 | 70 | | 6–7 | 150 |
| 13.5–15 | 77.5 | | 5–6 | 175 |
| 12–13.5 | 85 | | 4–5 | 200 |
| | | | < 4 | 250+ (250/300/400/500 by finer bands) |

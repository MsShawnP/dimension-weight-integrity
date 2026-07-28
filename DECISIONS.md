# Dimension & Weight Integrity — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-06-04 — Frontend: React 19 + TypeScript + Vite 6 + Cloudflare Pages
- **Why:** Discovery narrative requires state management for quiz/toggle interactions. React handles this naturally. Vite 6 bundles to static assets. Cloudflare Pages serves them with no origin server.
- **Scope:** `frontend/`
- **Do not:** Add a backend API. Frontend reads static JSON only.

### 2026-06-04 — Data loading: import-time JSON (Vite bundles small JSON into the app)
- **Why:** Hero + catalog JSON is small enough to inline. No runtime fetch, no loading states, no CORS. Simplest approach for static data.
- **Scope:** `frontend/src/data.ts`
- **Do not:** Use fetch() or public/ directory for data files.

### 2026-06-04 — Pipeline: Python data gen → Postgres raw → dbt (staging/intermediate/marts) → JSON export
- **Why:** Extends the existing Cinderhaven Data Platform (Postgres + dbt + Dagster on Fly.io). Real infrastructure, not scaffolding.
- **Scope:** Global

### 2026-06-04 — Dagster orchestrates the full pipeline as a single asset graph
- **Why:** Matches existing platform patterns. Asset graph: generate → load → dbt build → export JSON.
- **Scope:** `dagster/`

---

## Data & Schema

### 2026-06-04 — This piece owns physical-attribute fields; Product Data Health Audit owns structural completeness
- **Why:** Prevents two models from writing the same dimension fields. Clear ownership boundary.
- **Scope:** Global — all models touching unit_*_weight, case_gross_weight, case_cube, length/width/height, ti, hi
- **Do not:** Let any other piece's models write these fields.

### 2026-06-04 — 50 SKUs, not 90
- **Why:** Build spec's 90-SKU figure was incorrect. Cinderhaven SSOT has exactly 50 SKUs across 5 product lines.
- **Scope:** Global
- **Do not:** Reference 90 SKUs anywhere.

### 2026-06-04 — Synthetic data is seeded and deterministic
- **Why:** Same seed produces identical outputs across runs. Reproducibility for testing and demos.
- **Scope:** `data_gen/`

---

## Visualization

### 2026-06-04 — Discovery narrative over dashboard
- **Why:** The piece is a guided journey (quiz → reveal → cost → paradox → resolution → explore), not a self-serve analytics tool. Engagement and discovery moment are the portfolio value.
- **Scope:** `frontend/`
- **Do not:** Build a dashboard with filters and dropdowns. The viewer follows a story.

---

## Output Formats

### 2026-06-04 — Static JSON artifacts exported from dbt marts
- **Why:** Frontend never connects to a database. JSON is the contract between pipeline and frontend.
- **Scope:** `scripts/export_frontend_json.py` → `frontend/src/data/`

---

## Cost Parameters

### 2026-06-04 — Industry-benchmarked costs, honestly framed
- **Why:** Cost parameters are modeled from industry norms (carrier rate cards, NMFC density tables, chargeback surveys), not firsthand client data. Stated transparently.
- **Scope:** `config/cost_parameters.yml`
- **Do not:** Claim these represent actual client losses.

### 2026-06-04 — Exact vs parameter split as credibility core
- **Why:** Physics and standards are computed (never asserted as constants). Business parameters are config (flagged, calibratable, centralized). This distinction is the piece's claim to rigor.
- **Scope:** Global

---

## Writing & Voice

[Economist style per global CLAUDE.md]

---

## Testing

### 2026-06-04 — Vitest with globals: true for @testing-library/react compatibility
- **Why:** @testing-library/react auto-registers afterEach cleanup hooks by detecting the test framework's globals. Without `globals: true` in vitest config, cleanup doesn't run and DOM accumulates between tests, causing false failures.
- **Scope:** `frontend/vite.config.ts`
- **Do not:** Remove `globals: true` from vitest config — tests will silently break.

### 2026-06-04 — E2E reconciliation tests verify hero.json against physics and cost math
- **Why:** hero.json is the contract between pipeline and frontend. Tests verify AE1–AE4 invariants (physical constants, GDSN mismatch, cost driver math, rate tables) hold regardless of data source.
- **Scope:** `tests/test_e2e_reconciliation.py`

### 2026-06-04 — All business parameters sourced from dbt vars, not hard-coded in SQL
- **Why:** Code review found rate tables, annual volumes, chargeback costs, tolerances, DIM divisor, and packaging offset hard-coded in 4 SQL files — violating the "exact vs parameter split is the credibility core" rule. Values now flow from config/cost_params.yml → dbt_project.yml vars → SQL via `{{ var('...') }}` and the new `rate_lookup.sql` macro.
- **Scope:** `dbt/dbt_project.yml`, `dbt/macros/rate_lookup.sql`, `dbt/models/marts/fct_dimension_cost.sql`, `dbt/models/intermediate/int_dim_and_billable.sql`, `dbt/models/intermediate/int_system_attribute_divergence.sql`, `dbt/models/marts/fct_attribute_divergence.sql`
- **Do not:** Hard-code business parameters in SQL. All calibratable values go through dbt vars.

### 2026-06-04 — Runtime type assertions for JSON imports, not `as unknown as T`
- **Why:** Double-cast `as unknown as T` bypasses TypeScript entirely. Runtime assertion functions validate JSON shape at import time and fail fast with clear errors if the contract breaks.
- **Scope:** `frontend/src/data.ts`
- **Do not:** Use `as unknown as T` for JSON imports.

### 2026-06-04 — DB connection factory lives in data_gen/shared.py only
- **Why:** Three identical copies existed (data_gen, dagster, scripts). Single source prevents drift.
- **Scope:** `data_gen/shared.py`, `dagster/assets.py`, `scripts/export_frontend_json.py`
- **Do not:** Create new connection factories — import `get_db_connection` from `data_gen.shared`.

---

## Deployment

### 2026-06-04 — Frontend deployed to Cloudflare Pages at dimensions.lailarallc.com
- **Why:** Matches existing Cinderhaven portfolio pattern (audit.lailarallc.com, sku.lailarallc.com, etc.). Static assets served from Cloudflare edge, no origin server.
- **Scope:** `frontend/` deployment
- **Do not:** Deploy to a different platform or change the subdomain without updating README and cross-references.

---

## Metrics & Narrative Integrity

### 2026-07-27 — A published metric counts the population its label names, not the subset that costs money
- **Why:** `skus_with_class_mismatch` counted SKUs with `ltl_reclass annual_cost > 0`, so 7 downward freight-class shifts — real mismatches whose cost floors at $0 — were excluded. The live KPI read "SKUs with freight class mismatch: 20" when the true count was 27. Costed-subset counting is an easy, invisible way to publish a false number on a credibility-core deliverable.
- **Scope:** `scripts/export_frontend_json.py` aggregates; any metric surfaced in the frontend or README
- **Do not:** Derive a count from a cost being non-zero. Count the condition the label describes, and if the costed subset is also interesting, publish it as its own separately-labelled metric.

### 2026-07-27 — User-facing prose is derived from pipeline data, never hard-coded
- **Why:** Three separate stale-number bugs appeared in one session: the "$20,000 a year" hero lede, the wrong hero SKU name in the README, and the cost-driver explanations hard-coding densities, classes, and weights the pipeline already ships in `driver.basis`. Any figure typed into prose silently drifts the moment the pipeline changes.
- **Scope:** `frontend/src/components/**`, README, `index.html` meta
- **Do not:** Type a number into copy that the data already provides. Bind it to the JSON, or if it genuinely must be static, add a test that asserts it still matches the data.

### 2026-07-27 — Verify published figures against source data before reviewing code
- **Why:** Two wrong numbers reached the live CFO-facing site — the portfolio total was overstated by $2,680 ($20,213 vs $17,533), and "SKUs with freight class mismatch" published 20 when the true count was 27. Both survived multiple careful code reviews, because neither was a code defect a reader could spot: each was a mismatch between what the code computed and what the label or prose claimed. Recomputing the published figures independently from `data/generated/*.csv` found both in minutes. Reviewer agents also reported "both suites pass green" while 10 tests were erroring, because they spot-ran files instead of the full suite.
- **Scope:** Any `/improve`, code review, or UI review on this project
- **Do not:** Treat "the code looks correct" as evidence that a published number is correct. Recompute every figure the site displays from source data first, then read code only to explain a gap. Do not trust a reported test status without running the full suite yourself.

### 2026-07-27 — Calibratable parameters are documented with their sensitivity, not tuned to move the answer
- **Why:** `dtc_parcel_box_in` looked wrong because actual weight always beat DIM weight. It isn't: DIM only bills below `1728/139 = 12.43 lb/ft³`, and these jars run 11.6–24.4, so a dense product correctly bills on actual weight. But the parameter is a cliff — 5in and 6in both yield $9,988, 7in yields $13,228, 8in $19,372 — so raising it without evidence would manufacture cost while looking like a fix.
- **Scope:** `config/cost_params.yml`, `dbt/dbt_project.yml` vars
- **Do not:** Change a PARAM value to make a number look better. Document the crossover math and the sensitivity range, and leave the value until real client data justifies a change. Tag values no model reads as REFERENCE ONLY so wiring gaps are distinguishable from intentional documentation.

### 2026-07-28 — Verify a review finding's diagnosis before implementing its fix
- **Why:** Three findings in one Tier C fix list were wrong in ways that would have shipped bad work. The Critical prescribed repricing the LTL delta onto a pallet weight and generating a `ti`/`hi` field — but LTL bills per hundredweight, so `cases_per_pallet` cancels out of the cost and `per_unit_delta` was already correct; only the multiplier was wrong. A second claimed "all four committed CSVs break any Linux checkout" when `data/generated/` is gitignored and was never committed. A third prescribed HK-5 text on HK-35 pills, which measures 3.03:1 — worse than the 4.02:1 it would replace. Each was refuted in under two minutes by computing the quantity directly (the algebra, `git ls-files`, a WCAG ratio). Findings are plausible and specific, which is exactly what makes them persuasive enough to implement unchecked.
- **Scope:** Any handed-down fix list, review finding, or agent report on this project
- **Do not:** Implement a finding's prescribed fix because its problem statement is convincing. Recompute the asserted quantity first, and verify the proposed fix is better than the status quo — not just that the status quo is broken. When a finding doesn't survive, say so plainly and record the correction beside the original.

### 2026-07-28 — Annual volumes are derived from disclosed figures, not asserted
- **Why:** The LTL driver's entire magnitude rested on `annual_pallet_shipments_per_sku`, an unsourced count shipped at 52 while the build spec illustrated 520 — a 10x spread with no basis for either, which compounded with a second unsourced choice into a ~400x range on the headline. Replacing it with a derivation from figures the Cinderhaven dataset already publishes ($25M revenue ÷ 50 SKUs ÷ a wholesale unit price ÷ the SKU's own `case_pack_qty`) reduced that to one calibratable price with a real source, and the price itself comes from the seed catalog (mean MSRP $7.67 × blended non-DTC wholesale multiplier 0.5000 = $3.84/unit).
- **Scope:** `config/cost_params.yml`, `dbt/dbt_project.yml` vars — volume parameters in any cost driver
- **Do not:** Introduce a free-floating annual volume count. Derive it from a canonical figure plus a sourced price, and if a volume genuinely must be asserted, say so in the comment and name what would calibrate it. Note `annual_dtc_orders_per_sku` is still asserted and flagged as the parcel lane's highest-leverage assumption.

### 2026-07-28 — Check the billing unit before repricing a cost driver
- **Why:** The defect was a unit mismatch — a $/case figure multiplied by a count of pallet shipments — not a wrong basis. It read as a basis error because the two factors were separated by 20 lines and neither named its unit. Writing the units out made both the fix and the cancellation obvious, and showed that the "52 vs 520 pallets" question was the wrong axis entirely.
- **Scope:** `dbt/models/marts/fct_dimension_cost.sql` and any new cost driver
- **Do not:** Add a per-unit delta and an annual multiplier without stating both units in a comment adjacent to each. A driver's `per_unit_delta` and its `annual_units` must be in the same unit, and the carrier's actual billing basis (per cwt, per shipment, per event) decides which unit that is.

---

## Reversed / Superseded

[None yet]

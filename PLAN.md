# Dimension & Weight Integrity — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build the dimension & weight integrity piece: synthetic data generation,
dbt pipeline, cost computation, and discovery-narrative frontend.

## Why this arc, why now

Brainstorm and plan are complete. The piece is ready to build.
Implementation plan at `docs/plans/2026-06-04-001-feat-dimension-weight-integrity-plan.md`.

## Business question this arc answers

How much does inconsistent product dimension and weight data cost
Cinderhaven per year, and why can't you fix it by patching one system
at a time?

## Tasks

- [x] Run `/ce:brainstorm` to challenge and refine the build spec
- [x] Run `/ce:plan` to create an implementation plan
- [x] Lock stack decisions in DECISIONS.md
- [x] Run `/ce:work` to implement (15 units: U1–U15)
- [x] Run `/ce:review` — 17 findings, all resolved

## Out of scope for this arc

- Real client data (synthetic only)
- Mobile-first design
- User-adjustable rate parameters
- Multi-tenant / SaaS architecture

## Definition of done for this arc

- [x] Brainstorm doc produced and reviewed
- [x] Implementation plan produced with task breakdown
- [x] Stack decisions locked in DECISIONS.md
- [x] All 15 implementation units complete and verified
- [x] dbt tests pass, frontend deploys to Cloudflare Pages

---

## Arc history

### 2026-06-04 — Brainstorm + Plan arc (completed)
- Brainstormed from build spec → requirements doc at `docs/brainstorms/dimension-weight-integrity-requirements.md`
- Planned from requirements → plan at `docs/plans/2026-06-04-001-feat-dimension-weight-integrity-plan.md`
- Doc review applied 2 fixes, surfaced 22 findings (10 P1 decisions, 2 proposed fixes, 10 P2 decisions, 2 FYI)

---

## Improvement history

<!-- Entries are added by /improve — don't delete this section -->

### 2026-06-05 — Improvement pass
- **Trigger:** First /improve — just-shipped project, live-readiness check
- **What was reviewed:** Dependencies, index.html meta tags, README accuracy, DECISIONS.md accuracy, font bundle size, git hygiene
- **What was fixed:** Vitest critical vulnerability (3.x → 4.1.8), added meta description + OG tags to index.html, added live URL to README, corrected Workers → Pages in README/DECISIONS/PLAN, corrected Vite 8 → Vite 6 in DECISIONS.md, subset fonts to latin-only (CSS 22.5 KB → 13.0 KB), ran npm audit + pip-audit (both clean)
- **Deferred:** None — all 8 findings resolved
- **Next review:** 2026-07-05

### 2026-07-27 — Improvement pass (/improve + /code-review + /ui-review)
- **Trigger:** User-initiated combined pass. User concerns: (1) a CEO/CFO should grasp the tool's purpose in ≤30s, (2) confidence in AI-written code quality, (3) do not touch the Postgres source-of-truth DB.
- **What was reviewed:** 4 parallel reviewers (correctness, maintainability, testing, security-sentinel) + manual audit + UI review against the 30-second-CFO bar. Full pytest run surfaced a pre-existing broken test.
- **What was fixed (12 items, 12 commits):**
  - **#0** Restored green Python baseline — `test_data_gen` helper generated `CHP-{i:04d}` SKUs that never matched `HERO_SKU_ID` "CHP-AS-002" → `StopIteration` errored all 10 tests.
  - **#1** Stale NMFC freight-class table in `test_cost_math.py` asserted wrong classes (3.5→200, 0.5→400 vs correct 250/500); synced to canonical dbt/domain table.
  - **#2** DTC parcel DIM-weight used case dims as the single-unit box → overstated portfolio total; now uses `dtc_parcel_box_in` PARAM. **Rebuilt** against a throwaway local pg16 DB (native Postgres per documented workaround — Docker is broken here) from the committed raw CSVs: portfolio aggregate corrected **$20,213 → $17,533** (~$2,680 / 13% overstatement removed). all_skus.json regenerated; hero unaffected.
  - **#3** Removed dead client-side physics layer in `domain.ts` (8 unused fns + NMFC_BANDS) and the unused `rate_tables` payload from hero.json/export/types.
  - **#5** Added NMFC Python↔dbt drift guard + flagged-tolerance data test.
  - **#7** Removed dead imports/constant + duplicated `chapterIndex` helper.
  - **#8** Deduped raw-load routine (script vs Dagster asset) into `shared.load_csvs_to_raw`; consolidated 4 `query_*` fns; fixed a connection leak.
  - **#9** Dropped an inert test (asserted Python's own KeyError).
  - **#10** New test enforces `cost_params.yml` ↔ `dbt_project.yml` stay in sync.
  - **#11** `npm audit fix` (7 dev-only advisories → 0); added pinned `requirements.txt`.
  - **#4/#6/#12** Reworked hero: annual cost is now a 64px headline number (bound to data), Red-42 eyebrow, leads with the finding, and a new "Why would four systems disagree?" explainer up front (the user's #12 addition). Verified desktop + mobile against Lailara design system.
- **Deferred:** None — all 12 items resolved, including #2's rebuild (done via throwaway pg16 DB same session).
- **Next review:** 2026-10-25 (project is stable/shipped — 90-day cadence)

### 2026-07-27 — Post-change re-review (workflow: 35 agents)
- **Trigger:** User asked to re-run improve + code review + UI review after the dbt/data/frontend changes landed.
- **Method:** 7 parallel reviewers (data integrity, dbt correctness, Python, frontend, tests, security, narrative), every finding adversarially verified by an independent skeptic, then synthesized. **27 findings raised, 14 refuted, 13 survived** (7 severities corrected downward). Browser flow verified separately by hand.
- **Confirmed clean:** aggregate reconciles to the cent (50 SKU totals = 17533.48; 0 mismatches across 150 driver rows); the parcel fix is surgical (exactly 9 rows changed, summing to exactly $2,680.00); billable-weight distribution {2:20, 3:28, 4:2} with nothing at 5 lb (no case-box residue); physics computed not asserted; like-to-like holds; zero nulls/NaN/negatives. Full chapter flow, both paradox toggles, nav locking, and mobile all verified live.
- **What was fixed (3 important):**
  - **KPI was wrong on the live site.** `skus_with_class_mismatch` counted costly mismatches (20) not actual ones (**27**) — 7 downward class shifts are real mismatches floored to $0. Now counted from `fct_freight_class_by_system`, with a test recomputing it from the GDSN CSV.
  - **Modeled rates attributed to a third party.** CostReveal claimed a "Red Stag Fulfillment rate index"; config calls those rates a modeled stand-in. Corrected (and the parcel discount is now labelled modeled).
  - **Portfolio table was mouse-only.** Sorting/row-expansion had no keyboard path (WCAG 2.1.1). Headers are now real buttons with `aria-sort`; rows are focusable with Enter/Space and `aria-expanded`. 3 tests added.
- **Nice-to-have sweep (all cleared, same session):**
  - Removed unused `import os` and the stale export-script docstring; unpinned `dagster-dbt`/`dagster-postgres` (nothing imports them, no `dagster.yaml`).
  - Relabelled four unwired PARAMs as REFERENCE ONLY and documented why divergence flagging is absolute-tolerance only.
  - **Documented the parcel assumptions.** `dtc_parcel_box_in` is a cliff, not a dial: DIM weight only bills below `1728/139 = 12.43 lb/ft³` and these jars are denser, so 5in and 6in both give $9,988 while 7in gives $13,228 and 8in $19,372 — the shipped figure is the DIM-never-binds floor. Also flagged `annual_dtc_orders_per_sku`'s one-unit-per-order assumption as the highest-leverage uncertainty in that lane. Value deliberately left at 6.0 (changing it without evidence would manufacture cost).
  - **Hardened the NMFC drift guard.** It scanned for the right numbers only; it now strips Jinja comments and asserts a single compared expression, no extra `when` branches, and strictly descending thresholds. Verified against three sabotaged macros the old version accepted. (Note: the reviewer's claimed false-green vectors were mostly already caught — the real gap was that it never checked *what* was being compared.)
  - Added 5 tests covering `all_skus.json` (aggregate reconciliation, per-row driver sums, driver math, no negative costs, no SKU reaching the class-500 null-density fallback).
  - Deepened `data.ts` import-time guards to validate the shapes components actually index into.
  - **Corrected the ERP quiz annotation** — it claimed "net weight stored in gross field" beside a card showing 20.00 lb, which is neither the unit net (1.00) nor case net (12.00); the hero takes the "biased low ~7% + rounded dims" path.
  - **Bound the cost-driver prose to `driver.basis`** so the explanations can no longer drift from the numbers — the same failure mode behind the $20,000 lede and the wrong hero SKU name.
- **Final state:** 57 Python + 41 frontend tests pass, build clean.

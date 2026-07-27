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
  - **#2** DTC parcel DIM-weight used case dims as the single-unit box → overstated portfolio total; now uses `dtc_parcel_box_in` PARAM. **Code-only — marts/JSON not regenerated (Postgres down); the $20,213 figure updates on next `dbt build` + export.**
  - **#3** Removed dead client-side physics layer in `domain.ts` (8 unused fns + NMFC_BANDS) and the unused `rate_tables` payload from hero.json/export/types.
  - **#5** Added NMFC Python↔dbt drift guard + flagged-tolerance data test.
  - **#7** Removed dead imports/constant + duplicated `chapterIndex` helper.
  - **#8** Deduped raw-load routine (script vs Dagster asset) into `shared.load_csvs_to_raw`; consolidated 4 `query_*` fns; fixed a connection leak.
  - **#9** Dropped an inert test (asserted Python's own KeyError).
  - **#10** New test enforces `cost_params.yml` ↔ `dbt_project.yml` stay in sync.
  - **#11** `npm audit fix` (7 dev-only advisories → 0); added pinned `requirements.txt`.
  - **#4/#6/#12** Reworked hero: annual cost is now a 64px headline number (bound to data), Red-42 eyebrow, leads with the finding, and a new "Why would four systems disagree?" explainer up front (the user's #12 addition). Verified desktop + mobile against Lailara design system.
- **Deferred:** #2's pipeline rebuild — the SQL fix is committed but the shipped `hero.json`/`all_skus.json` still hold the old numbers until the user runs `dbt build` + `export_frontend_json.py` against their Postgres. Security review's Python-manifest gap resolved by #11.
- **Next review:** 2026-10-25 (project is stable/shipped — 90-day cadence)

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

## Reversed / Superseded

[None yet]

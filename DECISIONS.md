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

### 2026-06-04 — Frontend: React 19 + TypeScript + Vite 8 + Cloudflare Workers
- **Why:** Discovery narrative requires state management for quiz/toggle interactions. React handles this naturally. Vite 8 bundles to static assets. Cloudflare Workers serves them with no origin server.
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

## Reversed / Superseded

[None yet]

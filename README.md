# Dimension & Weight Integrity

One product, four systems, four different weights — this project measures exactly what that costs per year, and shows why no single-system fix makes it stop.

**Live:** https://dimensions.lailarallc.com

## What it does

Inconsistent product weights and dimensions across ERP, WMS, GDSN, and DTC systems silently bleed margin through freight misclassification, parcel reweigh back-bills, and compliance chargebacks. This project quantifies that cost for a 50-SKU specialty food portfolio and presents the finding as an interactive, executive-readable web story.

Under the hood it is a full data pipeline:

1. **Generate** — synthetic extracts of the same 50-SKU catalog as four systems see it: NetSuite (ERP), the warehouse WMS, GDSN (retail data sync), and Shopify (DTC)
2. **Reconcile** — dbt models establish the WMS physical measurement as the measurement of record and compute each system's divergence from it
3. **Cost** — freight class, dimensional weight, and chargeback exposure are computed per SKU from calibratable rate tables (`config/cost_params.yml`, every parameter source-cited)
4. **Present** — results export to JSON and render as a React narrative with interactive "fix this system" toggles

The four steps run as a Dagster asset graph: `generate_source_extracts → load_raw → dbt_build → export_frontend_json`.

## Why it matters

Each cost lane is billed by a different party, so no single report ever shows the total. For the hero SKU (CHP-0009, Calabrian Chili Marinara), which carries four conflicting physical representations across four systems:

- **LTL freight reclassification.** GDSN publishes inflated dimensions yielding density 37.98 lb/ft³ and freight class 55 instead of the correct class 50. Cost: $0.39/case × 52 pallets/yr = $20.28/yr.
- **Parcel reweigh back-billing.** Shopify lists ship weight as 1.00 lb (unit net weight). The actual parcel weighs 2.05 lb, billable at 3 lb. Cost: $1.97/shipment × 200 orders/yr = $394/yr.
- **Compliance chargebacks.** Published dimensions do not match physical measurement. Cost: $200/event × 1.2 expected events/yr = $240/yr, risk-adjusted for the ~40% of divergent SKUs that actually incur chargebacks.

Total annual cost for one SKU: $654.28.

The deeper finding is the **localization paradox**: fixing retail data (GDSN → physical) clears the LTL reclassification but leaves the DTC parcel leak. Fixing DTC data (Shopify → actual weight) clears parcel back-billing but leaves the LTL overcharge. No single-system toggle clears both — only a governed measurement of record does. The live frontend lets you flip each fix and watch the cost move.

## The Cinderhaven context

Built on the Cinderhaven synthetic dataset — a ~$25M specialty food brand, 50 SKUs across 5 product lines and 6 contracted retailers. The data is synthetic; the methodology, rate tables, and deliverables are real.

**Canonical baseline:** 50 SKUs · 5 product lines (AS·PS·SC·DG·SB) · 6 retailers (Walmart·Costco·Whole Foods·Sprouts·Kroger·Regional Group) · 10 channels (6 retail + UNFI·KeHE·DPI + DTC). Physical-attribute fields are owned by this project; the companion Product Data Health Audit owns structural completeness.

## Quick start

### Frontend only (no database required)

The frontend reads committed JSON exports in `frontend/src/data/`, so it runs standalone:

```
cd frontend
npm install
npm run dev
```

### Full pipeline (requires PostgreSQL)

Python dependencies: `dagster`, `dbt-postgres`, `psycopg2`, `pyyaml`. Postgres connection is configured by environment variables `CINDERHAVEN_DB_HOST` / `CINDERHAVEN_DB_PORT` / `CINDERHAVEN_DB_USER` / `CINDERHAVEN_DB_PASSWORD` / `CINDERHAVEN_DB_NAME` (defaults: `localhost:5432`, user `postgres`, database `cinderhaven`).

From the repo root:

```
export PYTHONPATH=.
dagster dev -f dagster/definitions.py
```

Then materialize all four assets from the Dagster UI. The steps can also run individually, e.g. `python -m data_gen.generate_dimension_mess` to regenerate the source CSVs into `data/generated/`.

### Tests

```
# Python tests (cost math, data generation, export, E2E reconciliation)
python -m pytest tests/ -v

# Frontend tests (Vitest)
cd frontend && npm test
```

## Tech stack

- **Pipeline:** Python 3.13, dbt-core, Dagster, PostgreSQL
- **Frontend:** React 19, TypeScript 5.7, Vite 6
- **Deployment:** Cloudflare Pages (frontend), Fly.io (pipeline)
- **Design:** Lailara design system (Playfair Display + Source Sans 3, Economist-style charts)

## Project structure

```
data_gen/     # Synthetic 50-SKU x 4-system extract generator (seeded, deterministic)
dagster/      # Asset graph orchestrating generate -> load -> dbt -> export
dbt/          # staging -> intermediate -> marts; physics (cube, density, freight class) in macros
scripts/      # Standalone loaders and the frontend JSON exporter
config/       # cost_params.yml — every rate, volume, and tolerance, with source citations
frontend/     # React story app with client-side paradox recomputation
tests/        # pytest suites for cost math, data gen, export, and E2E reconciliation
```

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.

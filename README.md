# Dimension & Weight Integrity

**Live:** https://dimensions.lailarallc.com

Inconsistent product weights and dimensions across ERP, WMS, GDSN, and DTC systems silently bleed margin through freight misclassification, parcel reweigh back-bills, and compliance chargebacks. This project quantifies the cost for Cinderhaven Foods' 50-SKU portfolio and demonstrates why no single-channel fix resolves the problem — only a governed measurement of record does.

## Cinderhaven context

Built on the Cinderhaven synthetic dataset — a ~$25M specialty food brand, 50 SKUs across 5 product lines and 6 contracted retailers. Data is synthetic; methodology and deliverables are real.

## What it finds

The hero SKU (CHP-0009, Calabrian Chili Marinara) carries four conflicting representations of its physical attributes across four systems. The WMS physical measurement (21.5 lb, 11.25×8.5×5.25″) is the measurement of record. Divergence from that record produces three cost drivers:

- **LTL freight reclassification.** GDSN publishes inflated dimensions yielding density 37.98 lb/ft³ and freight class 55 instead of the correct class 50. Cost: $0.39/case × 52 pallets/yr = $20.28/yr.
- **Parcel reweigh back-billing.** Shopify lists ship weight as 1.00 lb (unit net weight). Actual parcel weighs 2.05 lb, billable at 3 lb. Cost: $1.97/shipment × 200 orders/yr = $394/yr.
- **Compliance chargebacks.** Published dimensions do not match physical measurement. Cost: $200/event × 3 events/yr = $600/yr.

Total annual cost for one SKU: $1,014.28. The localization paradox: fixing retail data (GDSN → physical) clears LTL reclassification but leaves the DTC parcel leak. Fixing DTC data (Shopify → actual weight) clears parcel back-billing but leaves the LTL overcharge. No toggle state clears both. A governed measurement of record is the only configuration that does.

## Stack

- **Pipeline:** Python 3.13, dbt-core, Dagster, PostgreSQL
- **Frontend:** React 19, TypeScript 5.7, Vite 6
- **Deployment:** Cloudflare Pages (frontend), Fly.io (pipeline)
- **Design:** Lailara design system (Playfair Display + Source Sans 3, Economist-style charts)

## Data contract

**Canonical baseline:** 50 SKUs · 5 product lines (AS·PS·SC·DG·SB) · 6 retailers (Walmart·Costco·Whole Foods·Sprouts·Kroger·Regional Group) · 10 channels (6 retail + UNFI·KeHE·DPI + DTC)

Physical-attribute fields are owned by this project. Product Data Health Audit owns structural completeness.

## Run

### Frontend (development)

```
cd frontend
npm install
npm run dev
```

### Pipeline (requires PostgreSQL)

```
# Generate synthetic source data
python data_gen/generate_dimension_mess.py

# Load into Postgres and run dbt
cd dagster
dagster dev
```

### Tests

```
# Python tests (cost math, data generation, E2E reconciliation)
python -m pytest tests/ -v

# Frontend tests (50 tests across 7 suites)
cd frontend && npm test
```

---

Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.

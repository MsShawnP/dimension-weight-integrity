"""Generate synthetic per-system dimension/weight divergence for 50 Cinderhaven SKUs.

Reads product_master from platform Postgres, applies seeded divergence patterns
per system, and writes 4 CSV files to data/generated/. Deterministic — same seed
produces identical output.

Usage:
    python -m data_gen.generate_dimension_mess          # reads from Postgres
    python -m data_gen.generate_dimension_mess --cached  # reads from cached CSV
"""

import argparse
import copy
import csv
import math
import pathlib
import random

from data_gen.shared import DATA_DIR, HERO_SKU_ID, SEED

# Hero SKU build spec values (measurement of record)
HERO_MOR = {
    "case_gross_weight_lb": 21.50,
    "case_length_in": 11.25,
    "case_width_in": 8.50,
    "case_height_in": 5.25,
    "unit_net_weight_lb": 1.00,
    "case_pack_qty": 12,
}

# Typical case dimensions by pack qty for filling NULL-dimension SKUs
TYPICAL_CASE_DIMS = {
    6: {"length": 10.0, "width": 7.5, "height": 5.0},
    12: {"length": 12.0, "width": 9.0, "height": 6.0},
    24: {"length": 15.0, "width": 12.0, "height": 10.0},
}
DEFAULT_CASE_DIMS = {"length": 13.0, "width": 10.0, "height": 8.0}


def fill_missing_fields(products, rng):
    """Fill NULL case weights and dimensions with plausible synthetic values."""
    for p in products:
        unit_wt = p.get("unit_weight_lbs") or 0.75
        p["unit_weight_lbs"] = unit_wt
        pack_qty = p.get("case_pack_qty") or 12
        p["case_pack_qty"] = pack_qty

        if p.get("case_weight_lbs") is None:
            packaging_factor = 1.10 + rng.uniform(0, 0.10)
            p["case_weight_lbs"] = round(unit_wt * pack_qty * packaging_factor, 2)

        if any(p.get(k) is None for k in ("case_length_in", "case_width_in", "case_height_in")):
            base = TYPICAL_CASE_DIMS.get(pack_qty, DEFAULT_CASE_DIMS)
            jitter = lambda dim: round(dim * rng.uniform(0.90, 1.10), 2)
            p["case_length_in"] = p.get("case_length_in") or jitter(base["length"])
            p["case_width_in"] = p.get("case_width_in") or jitter(base["width"])
            p["case_height_in"] = p.get("case_height_in") or jitter(base["height"])

    return products


def apply_hero_overrides(products):
    """Override hero SKU with exact build spec values."""
    for p in products:
        if p["sku"] == HERO_SKU_ID:
            p["case_weight_lbs"] = HERO_MOR["case_gross_weight_lb"]
            p["unit_weight_lbs"] = HERO_MOR["unit_net_weight_lb"]
            p["case_length_in"] = HERO_MOR["case_length_in"]
            p["case_width_in"] = HERO_MOR["case_width_in"]
            p["case_height_in"] = HERO_MOR["case_height_in"]
            p["case_pack_qty"] = HERO_MOR["case_pack_qty"]
            break
    return products


def generate_wms(products, rng):
    """WMS = truth ± small scan noise (≤1% weight, ±0.25" dims)."""
    rows = []
    for p in products:
        wt = p["case_weight_lbs"]
        l, w, h = p["case_length_in"], p["case_width_in"], p["case_height_in"]

        if p["sku"] == HERO_SKU_ID:
            rows.append(_wms_row(p, wt, l, w, h))
        else:
            wt_noise = wt * rng.uniform(-0.01, 0.01)
            rows.append(_wms_row(
                p,
                round(wt + wt_noise, 2),
                round(l + rng.uniform(-0.25, 0.25), 2),
                round(w + rng.uniform(-0.25, 0.25), 2),
                round(h + rng.uniform(-0.25, 0.25), 2),
            ))
    return rows


def _wms_row(p, wt, l, w, h):
    return {
        "sku": p["sku"],
        "product_name": p["product_name"],
        "system": "wms",
        "case_gross_weight_lb": wt,
        "case_length_in": l,
        "case_width_in": w,
        "case_height_in": h,
        "unit_weight_lb": p["unit_weight_lbs"],
        "case_pack_qty": p["case_pack_qty"],
    }


def generate_erp(products, rng):
    """ERP (NetSuite): weight biased low 3-8%, dims rounded, ~20% unit/case confusion."""
    rows = []
    confusion_indices = set(rng.sample(range(len(products)), k=max(1, len(products) // 5)))

    for i, p in enumerate(products):
        wt = p["case_weight_lbs"]
        l, w, h = p["case_length_in"], p["case_width_in"], p["case_height_in"]

        if p["sku"] == HERO_SKU_ID:
            rows.append({
                "sku": p["sku"],
                "product_name": p["product_name"],
                "system": "erp",
                "case_gross_weight_lb": 20.00,
                "case_length_in": 11.0,
                "case_width_in": 8.0,
                "case_height_in": 5.0,
                "unit_weight_lb": 1.00,
                "case_pack_qty": p["case_pack_qty"],
            })
        else:
            bias = rng.uniform(0.03, 0.08)
            erp_wt = round(wt * (1 - bias), 2)
            erp_unit_wt = p["unit_weight_lbs"]

            if i in confusion_indices:
                erp_wt = erp_unit_wt

            rows.append({
                "sku": p["sku"],
                "product_name": p["product_name"],
                "system": "erp",
                "case_gross_weight_lb": erp_wt,
                "case_length_in": round(l),
                "case_width_in": round(w),
                "case_height_in": round(h),
                "unit_weight_lb": erp_unit_wt,
                "case_pack_qty": p["case_pack_qty"],
            })
    return rows


def generate_gdsn(products, rng):
    """GDSN (IX-ONE): dims inflated +10-25% on ~40%, weight rounded up to nearest 0.5."""
    rows = []
    inflate_indices = set(rng.sample(range(len(products)), k=max(1, int(len(products) * 0.4))))

    for i, p in enumerate(products):
        wt = p["case_weight_lbs"]
        l, w, h = p["case_length_in"], p["case_width_in"], p["case_height_in"]

        if p["sku"] == HERO_SKU_ID:
            rows.append({
                "sku": p["sku"],
                "product_name": p["product_name"],
                "system": "gdsn",
                "case_gross_weight_lb": 22.00,
                "case_length_in": 13.0,
                "case_width_in": 11.0,
                "case_height_in": 7.0,
                "unit_weight_lb": p["unit_weight_lbs"],
                "case_pack_qty": p["case_pack_qty"],
            })
        else:
            gdsn_wt = math.ceil(wt * 2) / 2
            if i in inflate_indices:
                l = round(l * rng.uniform(1.10, 1.25), 2)
                w = round(w * rng.uniform(1.10, 1.25), 2)
                h = round(h * rng.uniform(1.10, 1.25), 2)

            rows.append({
                "sku": p["sku"],
                "product_name": p["product_name"],
                "system": "gdsn",
                "case_gross_weight_lb": gdsn_wt,
                "case_length_in": round(l, 1),
                "case_width_in": round(w, 1),
                "case_height_in": round(h, 1),
                "unit_weight_lb": p["unit_weight_lbs"],
                "case_pack_qty": p["case_pack_qty"],
            })
    return rows


def generate_shopify(products, rng):
    """Shopify: ship_weight = net weight (systematic under-weight), dims null ~80%."""
    rows = []
    has_dims_indices = set(rng.sample(range(len(products)), k=max(1, len(products) // 5)))

    for i, p in enumerate(products):
        if p["sku"] == HERO_SKU_ID:
            rows.append({
                "sku": p["sku"],
                "product_name": p["product_name"],
                "system": "shopify",
                "ship_weight_lb": 1.00,
                "case_length_in": "",
                "case_width_in": "",
                "case_height_in": "",
                "unit_weight_lb": p["unit_weight_lbs"],
                "case_pack_qty": p["case_pack_qty"],
            })
        else:
            dims = {}
            if i in has_dims_indices:
                dims = {
                    "case_length_in": p["case_length_in"],
                    "case_width_in": p["case_width_in"],
                    "case_height_in": p["case_height_in"],
                }
            else:
                dims = {"case_length_in": "", "case_width_in": "", "case_height_in": ""}

            rows.append({
                "sku": p["sku"],
                "product_name": p["product_name"],
                "system": "shopify",
                "ship_weight_lb": p["unit_weight_lbs"],
                **dims,
                "unit_weight_lb": p["unit_weight_lbs"],
                "case_pack_qty": p["case_pack_qty"],
            })
    return rows


def write_csv(rows, filename):
    """Write rows to CSV in data/generated/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    if not rows:
        return path
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def generate_all(products):
    """Generate divergence data for all systems. Returns dict of system -> rows."""
    rng = random.Random(SEED)

    products = copy.deepcopy(products)
    products = fill_missing_fields(products, rng)
    products = apply_hero_overrides(products)

    wms = generate_wms(products, rng)
    erp = generate_erp(products, rng)
    gdsn = generate_gdsn(products, rng)
    shopify = generate_shopify(products, rng)

    write_csv(wms, "wms_dimensions.csv")
    write_csv(erp, "netsuite_items.csv")
    write_csv(gdsn, "gdsn_published.csv")
    write_csv(shopify, "shopify_products.csv")

    return {"wms": wms, "erp": erp, "gdsn": gdsn, "shopify": shopify}


def main():
    parser = argparse.ArgumentParser(description="Generate dimension divergence data")
    parser.add_argument("--cached", action="store_true", help="Read from cached CSV instead of Postgres")
    args = parser.parse_args()

    if args.cached:
        cache_path = DATA_DIR / "product_master_cache.csv"
        if not cache_path.exists():
            print(f"Error: cached file not found at {cache_path}")
            raise SystemExit(1)
        import csv as csv_mod
        with open(cache_path) as f:
            reader = csv_mod.DictReader(f)
            products = []
            for row in reader:
                for key in ("unit_weight_lbs", "case_weight_lbs", "case_length_in", "case_width_in", "case_height_in"):
                    row[key] = float(row[key]) if row.get(key) and row[key] != "" else None
                for key in ("case_pack_qty",):
                    row[key] = int(row[key]) if row.get(key) and row[key] != "" else None
                products.append(row)
    else:
        from data_gen.shared import fetch_product_master
        products = fetch_product_master()

    result = generate_all(products)
    total = sum(len(v) for v in result.values())
    print(f"Generated {total} rows across 4 systems ({len(result['wms'])} SKUs per system)")
    print(f"Output: {DATA_DIR}")


if __name__ == "__main__":
    main()

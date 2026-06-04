"""Export dbt mart data to static JSON for the frontend.

Queries Postgres marts, produces hero.json and all_skus.json with
embedded rate tables for client-side paradox recomputation.

Usage:
    python scripts/export_frontend_json.py
    python scripts/export_frontend_json.py --output-dir frontend/src/data
"""

import argparse
import decimal
import json
import os
import pathlib

import psycopg2
import psycopg2.extras
import yaml


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("CINDERHAVEN_DB_HOST", "localhost"),
        port=int(os.environ.get("CINDERHAVEN_DB_PORT", "5432")),
        user=os.environ.get("CINDERHAVEN_DB_USER", "postgres"),
        password=os.environ.get("CINDERHAVEN_DB_PASSWORD", ""),
        dbname=os.environ.get("CINDERHAVEN_DB_NAME", "cinderhaven"),
    )


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def load_config():
    config_path = pathlib.Path(__file__).parent.parent / "config" / "cost_params.yml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def query_governed_master(cur, sku=None):
    sql = "select * from public_marts.fct_governed_product_master"
    if sku:
        sql += " where sku = %s"
        cur.execute(sql, (sku,))
    else:
        cur.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def query_divergence(cur, sku=None):
    sql = "select * from public_marts.fct_attribute_divergence"
    if sku:
        sql += " where sku = %s"
        cur.execute(sql, (sku,))
    else:
        cur.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def query_freight_class(cur, sku=None):
    sql = "select * from public_marts.fct_freight_class_by_system"
    if sku:
        sql += " where sku = %s"
        cur.execute(sql, (sku,))
    else:
        cur.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def query_costs(cur, sku=None):
    sql = "select * from public_marts.fct_dimension_cost"
    if sku:
        sql += " where sku = %s"
        cur.execute(sql, (sku,))
    else:
        cur.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def build_hero_json(cur, hero_sku, config):
    master = query_governed_master(cur, hero_sku)
    if not master:
        raise ValueError(f"Hero SKU {hero_sku} not found in governed master")
    master = master[0]

    divergence = query_divergence(cur, hero_sku)
    freight = query_freight_class(cur, hero_sku)
    costs = query_costs(cur, hero_sku)

    systems = {}
    for row in divergence:
        sys = row["system"]
        if sys not in systems:
            systems[sys] = {"system": sys, "divergences": []}
        systems[sys]["divergences"].append({
            "field": row["field"],
            "system_value": row["system_value"],
            "mor_value": row["mor_value"],
            "abs_delta": row["abs_delta"],
            "pct_delta": row["pct_delta"],
            "flagged": row["flagged"],
        })

    freight_by_system = {}
    for row in freight:
        freight_by_system[row["system"]] = {
            "density": row["density_lb_per_ft3"],
            "freight_class": row["freight_class"],
        }

    cost_by_driver = {}
    for row in costs:
        cost_by_driver[row["cost_driver"]] = {
            "per_unit_delta": row["per_unit_delta"],
            "annual_units": row["annual_units"],
            "annual_cost": row["annual_cost"],
            "basis": row["basis"],
        }

    return {
        "hero_sku": {
            "sku": master["sku"],
            "product_name": master["product_name"],
            "measurement_of_record": {
                "source": master["mor_source"],
                "case_gross_weight_lb": master["case_gross_weight_lb"],
                "case_length_in": master["case_length_in"],
                "case_width_in": master["case_width_in"],
                "case_height_in": master["case_height_in"],
                "case_cube_ft3": master["case_cube_ft3"],
                "density_lb_per_ft3": master["density_lb_per_ft3"],
                "freight_class": master["freight_class"],
            },
            "systems": list(systems.values()),
            "freight_by_system": freight_by_system,
        },
        "cost": cost_by_driver,
        "rate_tables": {
            "ltl_rate_per_cwt": config["ltl"]["rate_per_cwt"],
            "parcel_rate_per_lb": config["parcel"]["rate_per_lb"],
            "dim_divisor": config["parcel"]["dim_divisor"],
        },
        "paradox": {
            "ops_fix": {
                "description": "Align GDSN dimensions to physical case measurements",
                "effect": "Retail freight class improves; DTC parcel leak unchanged",
            },
            "dtc_fix": {
                "description": "Correct Shopify weight to actual parcel gross weight",
                "effect": "Parcel back-billing eliminated; quoted shipping cost rises",
            },
        },
    }


def build_all_skus_json(cur, config):
    masters = query_governed_master(cur)
    costs = query_costs(cur)
    divergences = query_divergence(cur)

    cost_by_sku = {}
    for row in costs:
        sku = row["sku"]
        if sku not in cost_by_sku:
            cost_by_sku[sku] = {"drivers": {}, "total_annual_cost": 0}
        cost_by_sku[sku]["drivers"][row["cost_driver"]] = {
            "per_unit_delta": row["per_unit_delta"],
            "annual_units": row["annual_units"],
            "annual_cost": row["annual_cost"],
        }
        cost_by_sku[sku]["total_annual_cost"] += float(row["annual_cost"] or 0)

    div_by_sku = {}
    for row in divergences:
        sku = row["sku"]
        if sku not in div_by_sku:
            div_by_sku[sku] = []
        div_by_sku[sku].append({
            "system": row["system"],
            "field": row["field"],
            "abs_delta": row["abs_delta"],
            "flagged": row["flagged"],
        })

    skus = []
    for m in masters:
        sku = m["sku"]
        sku_cost = cost_by_sku.get(sku, {"drivers": {}, "total_annual_cost": 0})
        skus.append({
            "sku": sku,
            "product_name": m["product_name"],
            "case_gross_weight_lb": m["case_gross_weight_lb"],
            "freight_class": m["freight_class"],
            "density_lb_per_ft3": m["density_lb_per_ft3"],
            "cost": sku_cost,
            "divergence_count": len([d for d in div_by_sku.get(sku, []) if d["flagged"]]),
        })

    return {
        "skus": skus,
        "aggregate": {
            "total_annual_cost": sum(s["cost"]["total_annual_cost"] for s in skus),
            "skus_with_class_mismatch": sum(1 for s in skus if any(
                d.get("annual_cost", 0) and d.get("annual_cost", 0) > 0
                for d in s["cost"]["drivers"].values()
                if True
            )),
            "total_skus": len(skus),
        },
    }


def export(output_dir, hero_sku):
    config = load_config()
    conn = get_connection()

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            hero_data = build_hero_json(cur, hero_sku, config)
            all_skus_data = build_all_skus_json(cur, config)
    finally:
        conn.close()

    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    hero_path = output_path / "hero.json"
    with open(hero_path, "w") as f:
        json.dump(hero_data, f, cls=DecimalEncoder, indent=2)

    all_path = output_path / "all_skus.json"
    with open(all_path, "w") as f:
        json.dump(all_skus_data, f, cls=DecimalEncoder, indent=2)

    print(f"Exported hero.json ({hero_path.stat().st_size} bytes)")
    print(f"Exported all_skus.json ({all_path.stat().st_size} bytes)")
    return hero_path, all_path


def main():
    from data_gen.shared import HERO_SKU_ID

    parser = argparse.ArgumentParser(description="Export frontend JSON from dbt marts")
    parser.add_argument(
        "--output-dir",
        default="frontend/src/data",
        help="Output directory for JSON files",
    )
    args = parser.parse_args()
    export(args.output_dir, HERO_SKU_ID)


if __name__ == "__main__":
    main()

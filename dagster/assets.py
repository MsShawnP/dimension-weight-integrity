"""Dagster assets for the dimension & weight integrity pipeline.

Asset graph: generate_source_extracts → load_raw → dbt_build → export_frontend_json
"""

import csv
import os
import pathlib
import subprocess

from dagster import asset, AssetExecutionContext
from psycopg2 import sql

from data_gen.shared import get_db_connection


PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "generated"
DBT_DIR = PROJECT_ROOT / "dbt"
FRONTEND_DATA_DIR = PROJECT_ROOT / "frontend" / "src" / "data"

RAW_TABLES = {
    "netsuite_items": "netsuite_items.csv",
    "wms_dimensions": "wms_dimensions.csv",
    "gdsn_published": "gdsn_published.csv",
    "shopify_products": "shopify_products.csv",
}



@asset(description="Generate synthetic dimension divergence CSVs for 50 SKUs × 4 systems")
def generate_source_extracts(context: AssetExecutionContext):
    result = subprocess.run(
        ["python", "-m", "data_gen.generate_dimension_mess"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Data generation failed: {result.stderr}")
    context.log.info(result.stdout.strip())
    return {f: str(DATA_DIR / f) for f in RAW_TABLES.values()}


@asset(deps=[generate_source_extracts], description="Load generated CSVs into Postgres raw tables")
def load_raw(context: AssetExecutionContext):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for table_name, csv_file in RAW_TABLES.items():
                csv_path = DATA_DIR / csv_file
                context.log.info(f"Loading {csv_path} → {table_name}")

                with open(csv_path) as f:
                    reader = csv.DictReader(f)
                    columns = reader.fieldnames
                    tbl = sql.Identifier(table_name)
                    col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
                    col_defs = sql.SQL(", ").join(
                        sql.SQL("{} text").format(sql.Identifier(c)) for c in columns
                    )

                    cur.execute(sql.SQL("drop table if exists {}").format(tbl))
                    cur.execute(sql.SQL("create table {} ({})").format(tbl, col_defs))

                    placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
                    insert_stmt = sql.SQL("insert into {} ({}) values ({})").format(
                        tbl, col_ids, placeholders
                    )
                    for row in reader:
                        cur.execute(insert_stmt, [row[c] for c in columns])

                conn.commit()
                context.log.info(f"Loaded {table_name}")

            context.log.info(f"Loaded {len(RAW_TABLES)} raw tables")
    finally:
        conn.close()


@asset(deps=[load_raw], description="Run dbt build (models + tests)")
def dbt_build(context: AssetExecutionContext):
    result = subprocess.run(
        ["dbt", "build", "--profiles-dir", str(DBT_DIR), "--project-dir", str(DBT_DIR)],
        capture_output=True, text=True, cwd=str(DBT_DIR),
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"dbt build failed: {result.stderr}")


@asset(deps=[dbt_build], description="Export dbt marts to frontend JSON files")
def export_frontend_json(context: AssetExecutionContext):
    result = subprocess.run(
        ["python", "scripts/export_frontend_json.py", "--output-dir", str(FRONTEND_DATA_DIR)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Export failed: {result.stderr}")
    context.log.info(result.stdout.strip())

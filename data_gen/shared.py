"""Constants, RNG helpers, and DB connection for data generation."""

import decimal
import os
import pathlib

import psycopg2
import psycopg2.extras

SEED = 42

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "generated"

HERO_SKU_ID = "CHP-AS-002"
HERO_SKU_DISPLAY_NAME = "Roasted Garlic Marinara"

PRODUCT_MASTER_QUERY = """
    select
        sku,
        product_name,
        product_line,
        case_pack_qty,
        unit_weight_lbs,
        case_weight_lbs,
        case_length_in,
        case_width_in,
        case_height_in
    from raw.product_master
    where sku like 'CHP-%%'
    order by sku
"""


def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("CINDERHAVEN_DB_HOST", "localhost"),
        port=int(os.environ.get("CINDERHAVEN_DB_PORT", "5432")),
        user=os.environ.get("CINDERHAVEN_DB_USER", "postgres"),
        password=os.environ.get("CINDERHAVEN_DB_PASSWORD", ""),
        dbname=os.environ.get("CINDERHAVEN_DB_NAME", "cinderhaven"),
    )


def _coerce_numerics(row):
    """Convert Decimal/int to float for downstream arithmetic compatibility."""
    out = {}
    for k, v in row.items():
        if isinstance(v, decimal.Decimal):
            out[k] = float(v)
        elif k == "case_pack_qty" and v is not None:
            out[k] = int(v)
        else:
            out[k] = v
    return out


def fetch_product_master():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(PRODUCT_MASTER_QUERY)
            return [_coerce_numerics(row) for row in cur.fetchall()]
    finally:
        conn.close()

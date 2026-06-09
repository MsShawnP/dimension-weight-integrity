"""Load generated CSVs into Postgres raw tables (standalone, no Dagster)."""

import csv
from psycopg2 import sql
from data_gen.shared import get_db_connection, DATA_DIR

RAW_TABLES = {
    "netsuite_items": "netsuite_items.csv",
    "wms_dimensions": "wms_dimensions.csv",
    "gdsn_published": "gdsn_published.csv",
    "shopify_products": "shopify_products.csv",
}


def main():
    conn = get_db_connection()
    with conn.cursor() as cur:
        for table_name, csv_file in RAW_TABLES.items():
            with open(DATA_DIR / csv_file) as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                tbl = sql.Identifier(table_name)
                col_defs = sql.SQL(", ").join(
                    sql.SQL("{} text").format(sql.Identifier(c)) for c in columns
                )
                cur.execute(sql.SQL("drop table if exists {} cascade").format(tbl))
                cur.execute(sql.SQL("create table {} ({})").format(tbl, col_defs))
                placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
                col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
                insert_stmt = sql.SQL("insert into {} ({}) values ({})").format(
                    tbl, col_ids, placeholders
                )
                rows_loaded = 0
                for row in reader:
                    cur.execute(insert_stmt, [row[c] for c in columns])
                    rows_loaded += 1
            conn.commit()
            print(f"Loaded {table_name}: {rows_loaded} rows")
    conn.close()
    print("All raw tables loaded.")


if __name__ == "__main__":
    main()

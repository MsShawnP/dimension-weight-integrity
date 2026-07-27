"""Load generated CSVs into Postgres raw tables (standalone, no Dagster)."""

from data_gen.shared import get_db_connection, load_csvs_to_raw, RAW_TABLES, DATA_DIR


def main():
    conn = get_db_connection()
    try:
        load_csvs_to_raw(conn, DATA_DIR, RAW_TABLES)
    finally:
        conn.close()
    print("All raw tables loaded.")


if __name__ == "__main__":
    main()

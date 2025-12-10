"""
Load all L1d CSV rows into PostgreSQL for deterministic predictions.

Creates (if needed) table ld1_history matching the L1d schema and upserts
train/val/test rows. Values are stored as double precision; booleans are
mapped for heavy_rain_48h, is_flood, is_major_flood.
"""
import os
import sys
import csv
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "Data" / "processed" / "L1d"


def get_conn():
    host = os.environ.get("DB_HOST", "localhost")
    port = int(os.environ.get("DB_PORT", 5432))
    db = os.environ.get("DB_NAME", "flood_prediction")
    user = os.environ.get("DB_USER", "flood_user")
    pwd = os.environ.get("DB_PASSWORD", "flood_password")
    return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pwd)


def read_csv(path: Path):
    with path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows, reader.fieldnames


def ensure_table(cur, table: str, columns: list):
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} (date date PRIMARY KEY)")
    for col in columns:
        if col == "date":
            continue
        if col in ("heavy_rain_48h", "is_flood", "is_major_flood"):
            coltype = "boolean"
        else:
            coltype = "double precision"
        cur.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "{col}" {coltype}')


def boolify(val):
    if val in ("1", "True", "true", 1, True):
        return True
    if val in ("0", "False", "false", 0, False, "", None):
        return False
    return bool(val)


def main():
    files = ["train.csv", "val.csv", "test.csv"]
    rows_all = []
    fieldnames = None
    for fname in files:
        path = DATA_DIR / fname
        if not path.exists():
            print(f"Missing {path}, skipping")
            continue
        rows, cols = read_csv(path)
        fieldnames = cols if fieldnames is None else fieldnames
        rows_all.extend(rows)

    if not rows_all or not fieldnames:
        print("No rows loaded; aborting.")
        sys.exit(1)

    table = os.environ.get("LD1_TABLE", "ld1_history")

    conn = get_conn()
    cur = conn.cursor()
    ensure_table(cur, table, fieldnames)

    col_list = ','.join(f'"{c}"' for c in fieldnames)
    placeholder = ','.join(['%s'] * len(fieldnames))
    upsert_sql = f"""
        INSERT INTO {table} ({col_list}) VALUES ({placeholder})
        ON CONFLICT (date) DO UPDATE SET
        {', '.join([f'"{c}" = EXCLUDED."{c}"' for c in fieldnames if c != "date"])}
    """

    def row_to_tuple(row):
        out = []
        for c in fieldnames:
            val = row[c]
            if c == "date":
                out.append(val)
            elif c in ("heavy_rain_48h", "is_flood", "is_major_flood"):
                out.append(boolify(val))
            else:
                out.append(float(val) if val not in ("", None) else None)
        return tuple(out)

    execute_batch(cur, upsert_sql, [row_to_tuple(r) for r in rows_all], page_size=500)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(rows_all)} rows into {table}")


if __name__ == "__main__":
    main()

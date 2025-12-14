"""Load raw_dataset.csv into the raw_data table.

Usage:
    python load_raw_dataset.py [--csv /path/to/raw_dataset.csv]

Env vars (optional, defaults match docker-compose):
    DB_HOST=localhost
    DB_PORT=5439
    DB_NAME=flood_prediction
    DB_USER=flood_user
    DB_PASSWORD=flood_password

Requires: psycopg2-binary
"""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any, Dict

import psycopg2

DEFAULT_CSV = Path("../database/demo_data/raw_dataset.csv")
FEATURE_COLUMNS = [
    "daily_precip",
    "daily_temp_avg",
    "daily_snowfall",
    "daily_humidity",
    "daily_wind",
    "soil_deep_30d",
    "target_level_max",
    "hermann_level",
    "grafton_level",
]
MAX_MISSING_FEATURES = 2


def load_rows(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sanitized = sanitize_row(row)
            if sanitized is None:
                continue
            yield sanitized


def sanitize_row(row: Dict[str, Any]) -> Dict[str, Any] | None:
    missing = []
    for feature in FEATURE_COLUMNS:
        value = row.get(feature)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            missing.append(feature)
            row[feature] = 0
    if missing:
        date = row.get("date", "<unknown date>")
        print(
            f"Warning: {len(missing)} missing feature(s) for {date}; setting {', '.join(missing)} to 0"
        )
    if len(missing) > MAX_MISSING_FEATURES:
        print(
            f"Warning: dropping row for {row.get('date', '<unknown>')} because {len(missing)} features missing"
        )
        return None
    return row


def upsert_rows(conn, rows):
    sql = """
    INSERT INTO raw_data (
        date,
        daily_precip,
        daily_temp_avg,
        daily_snowfall,
        daily_humidity,
        daily_wind,
        soil_deep_30d,
        target_level_max,
        hermann_level,
        grafton_level,
        created_at
    ) VALUES (
        %(date)s,
        %(daily_precip)s,
        %(daily_temp_avg)s,
        %(daily_snowfall)s,
        %(daily_humidity)s,
        %(daily_wind)s,
        %(soil_deep_30d)s,
        %(target_level_max)s,
        %(hermann_level)s,
        %(grafton_level)s,
        NOW()
    )
    ON CONFLICT (date) DO UPDATE SET
        daily_precip = EXCLUDED.daily_precip,
        daily_temp_avg = EXCLUDED.daily_temp_avg,
        daily_snowfall = EXCLUDED.daily_snowfall,
        daily_humidity = EXCLUDED.daily_humidity,
        daily_wind = EXCLUDED.daily_wind,
        soil_deep_30d = EXCLUDED.soil_deep_30d,
        target_level_max = EXCLUDED.target_level_max,
        hermann_level = EXCLUDED.hermann_level,
        grafton_level = EXCLUDED.grafton_level,
        created_at = NOW();
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load raw_dataset.csv into raw_data table")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to raw_dataset.csv")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing rows from the `raw_data` table before loading the CSV",
    )
    args = parser.parse_args()

    csv_path = args.csv
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5439")),
        dbname=os.getenv("DB_NAME", "flood_prediction"),
        user=os.getenv("DB_USER", "flood_user"),
        password=os.getenv("DB_PASSWORD", "flood_password"),
    )

    try:
        rows = list(load_rows(csv_path))
        upsert_rows(conn, rows)
    finally:
        conn.close()

    print(f"Inserted/updated {len(rows)} rows into raw_data")


if __name__ == "__main__":
    main()

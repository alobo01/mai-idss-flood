"""Fetch ZIP code GeoJSON from ArcGIS and upsert into Postgres zip_geojson table.

Usage:
    python fetch_and_store_zip_geojson.py [--output path.geojson]

Env vars (optional, with defaults matching docker-compose):
    DB_HOST=localhost
    DB_PORT=5439
    DB_NAME=flood_prediction
    DB_USER=flood_user
    DB_PASSWORD=flood_password

Requires: requests, psycopg2-binary
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

import psycopg2
import requests

ARCGIS_URL = (
    "https://services7.arcgis.com/PUb8LWoYCB7TxITD/ArcGIS/rest/services/"
    "tl_2020_us_zcta510/FeatureServer/0/query"
)

ZIP_CODES: List[str] = [
    "63101","63102","63103","63104","63106","63107","63108","63109","63110","63111",
    "63112","63113","63115","63116","63118","63120","63133","63136","63137","63139",
    "63147","63155","63156","63157","63158","63163","63166","63169","63177","63178",
    "63179","63188",
]


def build_params() -> Dict[str, str]:
    where_clause = "ZCTA5CE10 IN ('" + "','".join(ZIP_CODES) + "')"
    return {
        "where": where_clause,
        "outFields": "*",
        "outSR": "4326",
        "f": "geojson",
    }


def fetch_geojson() -> Dict:
    params = build_params()
    resp = requests.get(ARCGIS_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def upsert_geojson(conn, features: List[Dict]):
    with conn.cursor() as cur:
        for feat in features:
            zip_code = (feat.get("properties") or {}).get("ZCTA5CE10")
            if not zip_code:
                continue
            geojson_text = json.dumps(feat)
            cur.execute(
                """
                INSERT INTO zip_geojson (zip_code, geojson, created_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (zip_code) DO UPDATE SET geojson = EXCLUDED.geojson, created_at = NOW();
                """,
                (zip_code, geojson_text),
            )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ZIP GeoJSON and store in Postgres.")
    parser.add_argument("--output", type=Path, default=None, help="Optional path to also write the GeoJSON file")
    args = parser.parse_args()

    data = fetch_geojson()
    features = data.get("features", [])

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data))

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5439")),
        dbname=os.getenv("DB_NAME", "flood_prediction"),
        user=os.getenv("DB_USER", "flood_user"),
        password=os.getenv("DB_PASSWORD", "flood_password"),
    )

    try:
        upsert_geojson(conn, features)
    finally:
        conn.close()

    print(f"Inserted/updated {len(features)} ZIP geojson features")


if __name__ == "__main__":
    main()

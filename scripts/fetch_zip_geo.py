"""Fetch ZIP code geographies from ArcGIS and store as GeoJSON.

Usage:
    python fetch_zip_geo.py [output_path]

Requires: requests
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List
import json
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


def build_params() -> dict:
    where_clause = "ZCTA5CE10 IN ('" + "','".join(ZIP_CODES) + "')"
    return {
        "where": where_clause,
        "outFields": "*",
        "outSR": "4326",
        "f": "geojson",
    }


def fetch_geojson(params: dict) -> bytes:
    resp = requests.get(ARCGIS_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.content


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("zip_zones.geojson")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    params = build_params()
    payload = fetch_geojson(params)
    output_path.write_bytes(payload)

    try:
        feature_count = len(json.loads(payload).get("features", []))
    except Exception:
        feature_count = "unknown"

    print(f"Saved {feature_count} features to {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate per-hour risk JSON snapshots from a CSV (e.g., Data/processed/L1d/test.csv).

The script maps the global probability to zone-level probabilities using the
shared pipeline_v3 helpers and writes risk_*.json files into both the backend
and public mock folders so the UI simulation can replay the real timeline.
"""
import csv
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = ROOT / "Source" / "frontend" / "backend"
MOCK_DIR = ROOT / "Source" / "frontend" / "public" / "mock"

# Make shared models importable
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from Models.zone_builder import compute_pf_by_zone_from_global  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Cannot import Models.zone_builder; run from repo root") from exc


def load_rows(csv_path: Path):
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def normalise(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(1.0, value / max_value)


def pick_drivers(row: dict) -> list:
    raw = [
        ("hermann_level", float(row.get("hermann_level", 0) or 0)),
        ("grafton_level", float(row.get("grafton_level", 0) or 0)),
        ("daily_precip", float(row.get("daily_precip", 0) or 0)),
    ]
    total = sum(abs(v) for _, v in raw) or 1.0
    return [
        {"feature": name, "contribution": round(abs(val) / total, 2)}
        for name, val in raw
    ]


def band(val: float) -> str:
    if val >= 0.75:
        return "Severe"
    if val >= 0.5:
        return "High"
    if val >= 0.35:
        return "Moderate"
    return "Low"


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "Data" / "processed" / "L1d" / "test.csv"
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    rows = load_rows(csv_path)
    max_target = max(float(r["target_level_max"]) for r in rows if r.get("target_level_max"))

    BACKEND_DIR.mkdir(parents=True, exist_ok=True)
    MOCK_DIR.mkdir(parents=True, exist_ok=True)

    timeline = []
    for row in rows:
        date_str = row["date"]
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12, minute=0, second=0)
        ts_str = dt.strftime("%Y-%m-%dT%H-%M-%SZ")
        global_pf = normalise(float(row["target_level_max"]), max_target)
        pf_by_zone = compute_pf_by_zone_from_global(global_pf)
        drivers = pick_drivers(row)
        eta = 6 if global_pf >= 0.6 else 12 if global_pf >= 0.4 else 18

        payload = [
            {
                "zoneId": zid,
                "risk": round(val, 3),
                "drivers": drivers,
                "thresholdBand": band(val),
                "etaHours": eta,
            }
            for zid, val in pf_by_zone.items()
        ]

        for outdir in (BACKEND_DIR, MOCK_DIR):
            (outdir / f"risk_{ts_str}.json").write_text(json.dumps(payload, indent=2))

        timeline.append(ts_str)

    # emit manifest for the UI simulation hook
    manifest = ROOT / "Source" / "frontend" / "src" / "hooks" / "riskTimeline.generated.ts"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w") as f:
        f.write("export const RISK_TIMELINE = [\n")
        for ts in timeline:
            f.write(f"  '{ts}',\n")
        f.write("];\n")

    print(f"Written {len(timeline)} snapshots to {BACKEND_DIR} and {MOCK_DIR}")
    print(f"Timeline manifest: {manifest}")


if __name__ == "__main__":
    main()

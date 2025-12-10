"""Produce an hourly merged dataset with target, upstream, and weather signals."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_v3.utils import (
    PROCESSED_DIR,
    RAW_DIR,
    ensure_dir,
    load_metadata,
    save_dataframe,
)

MERGED_PATH = PROCESSED_DIR / "merged_hourly.csv"


def _load_hourly_csv(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    return pd.read_csv(path, parse_dates=["time"])


def _build_hourly_frame(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    timeline = pd.date_range(start=start, end=end, freq="H")
    return pd.DataFrame({"time": timeline})


def _merge_target(base: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    merged = base.merge(target[["time", "target_level"]], on="time", how="left")
    merged = merged.sort_values("time").set_index("time")
    merged["target_level"] = merged["target_level"].interpolate(method="time").ffill().bfill()
    return merged.reset_index()


def _merge_upstream(base: pd.DataFrame, upstream: pd.DataFrame, level_col: str) -> pd.DataFrame:
    merged = base.merge(upstream[["time", level_col]], on="time", how="left")
    merged = merged.sort_values("time").set_index("time")
    merged[level_col] = merged[level_col].interpolate(method="time").ffill().bfill()
    return merged.reset_index()


def _merge_weather(base: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    weather_cols = [col for col in weather.columns if col != "time"]
    merged = base.merge(weather, on="time", how="left")
    merged[weather_cols] = merged[weather_cols].ffill().bfill()
    return merged


def main() -> None:
    metadata = load_metadata()
    target = _load_hourly_csv("target_hourly.csv")
    grafton = _load_hourly_csv("upstream_grafton.csv")
    hermann = _load_hourly_csv("upstream_hermann.csv")
    weather = _load_hourly_csv("weather_hourly.csv")

    start = target["time"].min()
    end = target["time"].max()
    hourly = _build_hourly_frame(start, end)

    merged = _merge_target(hourly, target)
    merged = _merge_upstream(merged, grafton, "grafton_level")
    merged = _merge_upstream(merged, hermann, "hermann_level")
    merged = _merge_weather(merged, weather)

    merged["precip_48h"] = merged["precipitation"].rolling(window=48, min_periods=1).sum()
    merged["heavy_rain_48h"] = (merged["precip_48h"] > 15).astype(int)

    merged["is_flood"] = (merged["target_level"] >= metadata["flood_stage"]).astype(int)
    merged["is_major_flood"] = (merged["target_level"] >= metadata["major_flood"]).astype(int)

    ensure_dir(MERGED_PATH.parent)
    save_dataframe(merged, MERGED_PATH)
    print(f"Saved hourly merge -> {MERGED_PATH}")


if __name__ == "__main__":
    main()

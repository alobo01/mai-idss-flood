"""Create daily engineered features from the merged hourly dataset."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_v3.utils import PROCESSED_DIR, load_metadata, save_dataframe

MERGED_PATH = PROCESSED_DIR / "merged_hourly.csv"
ENGINEERED_PATH = PROCESSED_DIR / "engineered_features.csv"


def _flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = ["_".join(col).strip("_") if isinstance(col, tuple) else col for col in frame.columns]
    return frame


def main() -> None:
    metadata = load_metadata()
    merged = pd.read_csv(MERGED_PATH, parse_dates=["time"])

    agg = merged.resample("D", on="time").agg(
        target_level_max=("target_level", "max"),
        target_level_mean=("target_level", "mean"),
        target_level_min=("target_level", "min"),
        target_level_std=("target_level", "std"),
        grafton_level=("grafton_level", "mean"),
        hermann_level=("hermann_level", "mean"),
        daily_precip=("precipitation", "sum"),
        daily_temp_avg=("temperature_2m", "mean"),
        daily_snowfall=("snowfall", "sum"),
        daily_humidity=("relative_humidity_2m", "mean"),
        daily_wind=("wind_speed_10m", "mean"),
        soil_moisture_0_to_7cm=("soil_moisture_0_to_7cm", "mean"),
        soil_moisture_7_to_28cm=("soil_moisture_7_to_28cm", "mean"),
        soil_moisture_28_to_100cm=("soil_moisture_28_to_100cm", "mean"),
        heavy_rain_48h=("heavy_rain_48h", "max"),
    )

    daily = agg.reset_index().rename(columns={"time": "date"})

    daily["precip_7d"] = daily["daily_precip"].rolling(window=7, min_periods=1).sum()
    daily["precip_14d"] = daily["daily_precip"].rolling(window=14, min_periods=1).sum()
    daily["precip_30d"] = daily["daily_precip"].rolling(window=30, min_periods=1).sum()
    daily["soil_deep_30d"] = (
        daily["soil_moisture_28_to_100cm"].rolling(window=30, min_periods=1).mean()
    )

    daily["is_flood"] = (daily["target_level_max"] >= metadata["flood_stage"]).astype(int)
    daily["is_major_flood"] = (
        daily["target_level_max"] >= metadata["major_flood"]
    ).astype(int)

    daily["date"] = pd.to_datetime(daily["date"])

    save_dataframe(daily, ENGINEERED_PATH)
    print(f"Saved engineered features -> {ENGINEERED_PATH}")


if __name__ == "__main__":
    main()

"""Load raw hydrologic + weather sources and align their time spans."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_v3.utils import RAW_DIR, REPO_ROOT as PIPELINE_REPO_ROOT, ensure_dir, load_metadata, save_dataframe


def _load_csv(relative_path: str) -> pd.DataFrame:
    path = PIPELINE_REPO_ROOT / relative_path
    df = pd.read_csv(path)
    return df


def _normalize_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.tz_localize(None)


def main() -> None:
    metadata = load_metadata()
    ensure_dir(RAW_DIR)

    target = _load_csv(metadata["target_file"])
    target["time"] = _normalize_datetime(target["time"])
    target = target.rename(columns={"usgs_level": "target_level"})

    upstream_frames = {}
    for name, rel_path in metadata["upstream_files"].items():
        frame = _load_csv(rel_path)
        frame["time"] = _normalize_datetime(frame["time"])
        upstream_frames[name] = frame

    weather = _load_csv(metadata["weather_file"])
    weather["datetime"] = _normalize_datetime(weather["datetime"])
    weather = weather.rename(columns={"datetime": "time"})

    # Align on the overlapping time window across all sources.
    min_end = min(
        target["time"].max(),
        *(frame["time"].max() for frame in upstream_frames.values()),
        weather["time"].max(),
    )
    max_start = max(
        target["time"].min(),
        *(frame["time"].min() for frame in upstream_frames.values()),
        weather["time"].min(),
    )

    def _clip(df: pd.DataFrame, time_col: str = "time") -> pd.DataFrame:
        return df[(df[time_col] >= max_start) & (df[time_col] <= min_end)].copy()

    target = _clip(target)
    for name, df in upstream_frames.items():
        upstream_frames[name] = _clip(df)
    weather = _clip(weather)

    save_dataframe(target, RAW_DIR / "target_hourly.csv")
    for name, df in upstream_frames.items():
        save_dataframe(df, RAW_DIR / f"upstream_{name}.csv")
    save_dataframe(weather, RAW_DIR / "weather_hourly.csv")

    print(
        "Loaded raw inputs spanning",
        max_start.strftime("%Y-%m-%d"),
        "to",
        min_end.strftime("%Y-%m-%d"),
    )


if __name__ == "__main__":
    main()

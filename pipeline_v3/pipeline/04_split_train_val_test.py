"""Create lead-specific feature matrices and temporal splits."""

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
    TRAIN_SPLIT_DIR,
    ensure_dir,
    load_hyperparameters,
    load_metadata,
    save_dataframe,
)

ENGINEERED_PATH = PROCESSED_DIR / "engineered_features.csv"

RELATIVE_LAGS = [0, 1, 2, 4, 6]
WEATHER_COLS = ["precip_7d", "precip_14d", "precip_30d", "soil_deep_30d", "daily_precip"]
ROLL_WINDOWS = [3, 7, 14]


def _build_lead_dataset(df: pd.DataFrame, lead: int) -> pd.DataFrame:
    frame = df.copy()
    for offset in RELATIVE_LAGS:
        actual = lead + offset
        frame[f"hermann_level_lag{actual}d"] = frame["hermann_level"].shift(actual)
        frame[f"grafton_level_lag{actual}d"] = frame["grafton_level"].shift(actual)
        if offset < 3:
            frame[f"target_level_max_lag{actual}d"] = frame["target_level_max"].shift(actual)

    for col in WEATHER_COLS:
        frame[f"{col}_lag{lead}d"] = frame[col].shift(lead)

    for window in ROLL_WINDOWS:
        frame[f"hermann_ma{window}d"] = frame["hermann_level"].shift(lead).rolling(window).mean()
        frame[f"grafton_ma{window}d"] = frame["grafton_level"].shift(lead).rolling(window).mean()

    frame = frame.dropna().reset_index(drop=True)
    return frame


def _split_by_date(df: pd.DataFrame, val_start: str, test_start: str):
    df["date"] = pd.to_datetime(df["date"])
    val_start_ts = pd.Timestamp(val_start)
    test_start_ts = pd.Timestamp(test_start)
    train = df[df["date"] < val_start_ts].copy()
    val = df[(df["date"] >= val_start_ts) & (df["date"] < test_start_ts)].copy()
    test = df[df["date"] >= test_start_ts].copy()
    return train, val, test


def main() -> None:
    metadata = load_metadata()
    hyperparams = load_hyperparameters()
    leads = hyperparams.get("lead_times", [1])

    base = pd.read_csv(ENGINEERED_PATH, parse_dates=["date"])

    for lead in leads:
        dataset = _build_lead_dataset(base, lead)
        split_dir = ensure_dir(TRAIN_SPLIT_DIR / f"L{lead}d")
        dataset_path = split_dir / f"dataset_L{lead}d.csv"
        save_dataframe(dataset, dataset_path)

        train, val, test = _split_by_date(dataset, metadata["val_start"], metadata["test_start"])
        save_dataframe(train, split_dir / "train.csv")
        save_dataframe(val, split_dir / "val.csv")
        save_dataframe(test, split_dir / "test.csv")
        print(f"Lead {lead}d: train={len(train)} val={len(val)} test={len(test)} rows saved")


if __name__ == "__main__":
    main()

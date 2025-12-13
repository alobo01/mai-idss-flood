#!/usr/bin/env python3
"""Extract previous N days from frontend raw test dataset for each use case file.

This script scans the use-case CSV filenames in `Data/processed/UseCaseData` for dates
and labels (e.g. `2019-03-31_major_flood.csv`), then extracts the last N days
from the frontend raw dataset (default 30 days, inclusive) and writes them as
`<date>_<label>_raw_data.csv` into the `usecase_dir`.

Usage:
    python Programs/extract_use_case_raw_data.py \
        --n_days 30 \
        --frontend_csv Data/frontend_raw_test.csv \
        --usecase_dir Data/processed/UseCaseData \
        --out_dir Data/processed/UseCaseData
"""

from __future__ import annotations

import argparse
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List

import pandas as pd


def find_usecase_files(usecase_dir: str) -> List[str]:
    """Return a list of filenames (not full path) that are use case csv files.

    Will ignore files that already end with `_raw_data.csv` to avoid re-processing.
    """
    files = []
    for entry in os.listdir(usecase_dir):
        if not entry.lower().endswith(".csv"):
            continue
        if entry.lower().endswith("_raw_data.csv"):
            # already processed file
            continue
        files.append(entry)
    return sorted(files)


def parse_filename(filename: str):
    """Parse filename of the format YYYY-MM-DD_label.csv and return date and label.

    Returns (date(datetime.date), label string). If parse fails, returns (None, None).
    """
    m = re.match(r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<label>.+?)\.csv$", filename)
    if not m:
        return None, None
    date_str = m.group("date")
    label = m.group("label")
    try:
        date = pd.to_datetime(date_str).date()
    except Exception:
        return None, None
    return date, label


def extract_window(df: pd.DataFrame, end_date: datetime.date, n_days: int, date_col: str = "date") -> pd.DataFrame:
    start_date = end_date - timedelta(days=n_days - 1)
    mask = (df[date_col] >= pd.Timestamp(start_date)) & (df[date_col] <= pd.Timestamp(end_date))
    return df.loc[mask].copy()


def main():
    parser = argparse.ArgumentParser(description="Extract previous N days for use cases from frontend dataset")
    parser.add_argument("--n_days", type=int, default=30, help="Number of previous days to include (inclusive of the use case date)")
    parser.add_argument("--frontend_csv", type=str, default="Data/frontend_raw_test.csv", help="Path to frontend raw CSV with date column named 'date'")
    parser.add_argument("--usecase_dir", type=str, default="Data/processed/UseCaseData", help="Directory with use case files (e.g., '2019-03-31_major_flood.csv')")
    parser.add_argument("--out_dir", type=str, default=None, help="Directory to write extracted raw files; defaults to usecase_dir")
    parser.add_argument("--date_col", type=str, default="date", help="Name of the date column in frontend CSV")
    parser.add_argument("--no_overwrite", action="store_true", help="Do not overwrite files that already exist in out_dir")
    args = parser.parse_args()

    out_dir = args.out_dir or args.usecase_dir
    if not os.path.isdir(args.usecase_dir):
        raise SystemExit(f"Usecase directory not found: {args.usecase_dir}")
    os.makedirs(out_dir, exist_ok=True)

    # Read frontend CSV
    logging.info("Reading frontend CSV: %s", args.frontend_csv)
    df = pd.read_csv(args.frontend_csv, parse_dates=[args.date_col])
    if df.empty:
        raise SystemExit("Frontend CSV appears empty")
    if args.date_col not in df.columns:
        raise SystemExit(f"Date column '{args.date_col}' not found in frontend CSV")

    # find use case files
    usecase_files = find_usecase_files(args.usecase_dir)
    if not usecase_files:
        logging.info("No use case files found in %s", args.usecase_dir)
        return

    logging.info("Found %d use case files", len(usecase_files))

    processed_count = 0
    for fname in usecase_files:
        date_val, label = parse_filename(fname)
        if date_val is None or label is None:
            logging.warning("Skipping file with unrecognized filename pattern: %s", fname)
            continue

        out_name = f"{date_val.isoformat()}_{label}_raw_data.csv"
        out_path = os.path.join(out_dir, out_name)
        if args.no_overwrite and os.path.exists(out_path):
            logging.info("Skipping existing file (no overwrite): %s", out_path)
            continue

        extracted = extract_window(df, date_val, args.n_days, date_col=args.date_col)
        if extracted.empty:
            logging.warning("No rows found in the target window for %s; file will not be created", fname)
            continue

        extracted.to_csv(out_path, index=False)
        logging.info("Wrote %s (%d rows)", out_path, len(extracted))
        processed_count += 1

    logging.info("Done. %d files processed.", processed_count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()

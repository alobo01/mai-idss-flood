#!/usr/bin/env python3
"""Builds standardized model inputs with schema + provenance controls."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Models.severity_mapping import FLOOD_STAGE, MAJOR_FLOOD_STAGE, level_to_global_pf

from pipeline_v2 import schema
from pipeline_v2.logging_utils import configure_logging
from pipeline_v2.provenance import build_provenance, write_manifest
from pipeline_v2.zone_registry import load_zone_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, help="Scenario defined in pipeline_v2/config.yaml")
    parser.add_argument("--config", default="pipeline_v2/config.yaml", help="Path to v2 config file")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    return parser.parse_args()


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"pipeline_v2 config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _detect_column(df: pd.DataFrame, candidates) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _timestamps(df: pd.DataFrame, scenario_cfg: Dict[str, Any], fallback_freq: int) -> pd.Series:
    column = scenario_cfg.get("timestamp_column") or _detect_column(df, ["timestamp", "time", "date"])
    if column:
        ts = pd.to_datetime(df[column])
        return ts.dt.tz_localize("UTC", nonexistent="NaT", ambiguous="NaT")
    start_ts = pd.Timestamp(scenario_cfg.get("start_timestamp", "2000-01-01T00:00:00Z"), tz="UTC")
    freq = pd.Timedelta(hours=int(scenario_cfg.get("forecast_horizon", fallback_freq)))
    return pd.Series([start_ts + i * freq for i in range(len(df))], index=df.index)


def _river_levels(df: pd.DataFrame, scenario_cfg: Dict[str, Any]) -> pd.Series:
    column = scenario_cfg.get("river_level_column")
    if column and column in df.columns:
        return pd.to_numeric(df[column], errors="coerce")
    meter_col = _detect_column(df, ["Water Level (m)", "river_level_m"])
    if meter_col:
        return pd.to_numeric(df[meter_col], errors="coerce") * 3.28084
    feet_col = _detect_column(df, ["river_level", "target_level", "target_level_mean", "target_level_max"])
    if feet_col:
        return pd.to_numeric(df[feet_col], errors="coerce")
    prob_col = scenario_cfg.get("probability_column") or "FloodProbability"
    if prob_col in df.columns:
        prob = pd.to_numeric(df[prob_col], errors="coerce").clip(0, 1)
        return FLOOD_STAGE + (MAJOR_FLOOD_STAGE - FLOOD_STAGE) * prob
    raise ValueError("Unable to derive river level for scenario; update config with 'river_level_column'")


def _global_probability(df: pd.DataFrame, scenario_cfg: Dict[str, Any], river_level: pd.Series) -> pd.Series:
    prob_col = scenario_cfg.get("probability_column")
    if prob_col and prob_col in df.columns:
        return pd.to_numeric(df[prob_col], errors="coerce").clip(0, 1)
    if "FloodProbability" in df.columns:
        return pd.to_numeric(df["FloodProbability"], errors="coerce").clip(0, 1)
    return river_level.apply(lambda level: level_to_global_pf(float(level)))


def main() -> None:
    args = parse_args()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    config_path = Path(args.config)
    config = load_config(config_path)
    scenarios = {entry["name"] if isinstance(entry, dict) else entry: entry for entry in config.get("scenarios", [])}
    if args.scenario not in scenarios:
        raise KeyError(f"Scenario '{args.scenario}' not found in config")
    scenario_cfg = scenarios[args.scenario] if isinstance(scenarios[args.scenario], dict) else {"name": args.scenario}

    processed_root = Path(config.get("paths", {}).get("processed", "Data/processed"))
    standardized_root = Path(config.get("paths", {}).get("standardized", "Data/processed_v2"))
    source_file = scenario_cfg.get("source_file")
    if not source_file:
        raise ValueError("Scenario config missing 'source_file'")
    source_path = processed_root / source_file
    if not source_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {source_path}")

    logging.info("Loading processed dataset for %s from %s", args.scenario, source_path)
    df = pd.read_csv(source_path)

    timestamps = _timestamps(df, scenario_cfg, config.get("forecast_horizon", 24))
    river_level = _river_levels(df, scenario_cfg)
    global_pf = _global_probability(df, scenario_cfg, river_level)

    if timestamps.isna().any():
        raise ValueError("Timestamp series contains NaT entries")
    if river_level.isna().any():
        raise ValueError("River level series contains NaN entries")
    if global_pf.isna().any():
        raise ValueError("Global probability contains NaN entries")

    zone_config_path = Path(scenario_cfg.get("zone_config", ""))
    if not zone_config_path:
        raise ValueError("Scenario config missing 'zone_config'")
    bundle = load_zone_file(args.scenario, zone_config_path)

    rows = []
    for idx in range(len(df)):
        ts = timestamps.iat[idx]
        river_val = float(river_level.iat[idx])
        pf_val = float(global_pf.iat[idx])
        for zone in bundle.zones.values():
            rows.append(
                {
                    "timestamp": pd.Timestamp(ts).isoformat(),
                    "scenario": args.scenario,
                    "zone_id": zone.id,
                    "river_level_pred": round(river_val, 4),
                    "global_pf": round(pf_val, 4),
                    "pf_zone": round(min(1.0, pf_val * zone.pf_weight), 4),
                    "vulnerability": zone.vulnerability,
                    "is_critical_infra": zone.is_critical_infra,
                }
            )

    model_input_df = pd.DataFrame(rows)
    errors = schema.validate_dataframe("model_input", model_input_df, schema.MODEL_INPUT_SCHEMA)
    if errors:
        raise ValueError("; ".join(errors))

    standardized_root.mkdir(parents=True, exist_ok=True)
    output_path = standardized_root / f"{args.scenario}_model_input.csv"
    model_input_df.to_csv(output_path, index=False)
    logging.info("Wrote standardized input to %s", output_path)

    provenance = build_provenance(args.scenario, config_path, source_path, Path.cwd())
    manifest_path = output_path.with_suffix(".meta.json")
    write_manifest(provenance, manifest_path)
    logging.info("Wrote provenance manifest to %s", manifest_path)


if __name__ == "__main__":
    main()

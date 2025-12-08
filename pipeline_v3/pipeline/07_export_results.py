"""Aggregate predictions and export evaluation scorecards."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Models.rule_based import allocate_resources
from Models.zone_builder import build_zones_from_config, compute_pf_by_zone_from_global
from Models.severity_mapping import level_to_global_pf

from pipeline_v3.utils import OUTPUTS_DIR, PREDICTIONS_DIR, ensure_dir, load_hyperparameters, load_metadata

TARGET_COL = "target_level_max"
MODEL_KEYS = ["P_XGB", "P_LSTM", "P_Bayesian", "P_final"]
RULE_BASED_DIR = OUTPUTS_DIR / "rule_based"


def _compute_metrics(actual: np.ndarray, preds: np.ndarray, flood_stage: float) -> dict:
    rmse = float(math.sqrt(np.mean((preds - actual) ** 2)))
    bias = float(np.mean(preds - actual))
    actual_flood = actual >= flood_stage
    pred_flood = preds >= flood_stage
    missed = int(np.logical_and(actual_flood, ~pred_flood).sum())
    false_alarms = int(np.logical_and(~actual_flood, pred_flood).sum())
    return {
        "RMSE": round(rmse, 3),
        "Bias": round(bias, 3),
        "Missed Floods": missed,
        "False Alarms": false_alarms,
    }


def _maybe_run_rule_based(df: pd.DataFrame, lead: int, rule_cfg: dict) -> None:
    if not rule_cfg.get("enabled", False):
        return

    total_units = int(rule_cfg.get("total_units", 0))
    if total_units <= 0:
        return

    allocation_mode = rule_cfg.get("allocation_mode", "crisp").lower()
    max_units = rule_cfg.get("max_units_per_zone")

    ensure_dir(RULE_BASED_DIR)
    records = []

    for row in df.itertuples(index=False):
        predicted_level = float(row.P_final)  # type: ignore[arg-type]
        global_pf = level_to_global_pf(predicted_level)
        pf_by_zone = compute_pf_by_zone_from_global(global_pf)
        zones = build_zones_from_config(pf_by_zone)
        zone_map = {zone.id: zone for zone in zones}

        allocations = allocate_resources(
            zones,
            total_units=total_units,
            mode=allocation_mode,
            max_units_per_zone=max_units,
        )

        for alloc in allocations:
            zone = zone_map[alloc["zone_id"]]
            records.append(
                {
                    "date": row.date,
                    "lead_time": f"{lead}d",
                    "predicted_level_ft": predicted_level,
                    "global_pf": round(global_pf, 4),
                    "zone_id": alloc["zone_id"],
                    "zone_name": alloc["zone_name"],
                    "zone_pf": round(zone.pf, 4),
                    "zone_vulnerability": round(zone.vulnerability, 4),
                    "impact_level": alloc["impact_level"],
                    "allocation_mode": alloc["allocation_mode"],
                    "units_allocated": alloc["units_allocated"],
                }
            )

    if records:
        out_path = RULE_BASED_DIR / f"L{lead}d_rule_based_allocations.csv"
        pd.DataFrame(records).to_csv(out_path, index=False)
        print(f"Saved rule-based allocations -> {out_path}")


def main() -> None:
    metadata = load_metadata()
    hyperparams = load_hyperparameters()
    leads = hyperparams.get("lead_times", [1])
    rule_cfg = metadata.get("rule_based", {})

    ensure_dir(OUTPUTS_DIR)
    metrics_records = []
    combined_predictions = []

    for lead in leads:
        pred_path = PREDICTIONS_DIR / f"L{lead}d_test_predictions.csv"
        df = pd.read_csv(pred_path)
        df["lead_time"] = lead
        combined_predictions.append(df)

        actual = df[TARGET_COL].to_numpy()
        for key in MODEL_KEYS:
            stats = _compute_metrics(actual, df[key].to_numpy(), metadata["flood_stage"])
            stats.update({"Lead Time": f"{lead}d", "Model": key})
            metrics_records.append(stats)

        if rule_cfg:
            _maybe_run_rule_based(df, lead, rule_cfg)

    scorecard = pd.DataFrame(metrics_records)
    scorecard.to_csv(OUTPUTS_DIR / "scorecard.csv", index=False)

    final_predictions = pd.concat(combined_predictions, ignore_index=True)
    final_predictions.to_csv(OUTPUTS_DIR / "pfinal_predictions.csv", index=False)

    print(f"Saved metrics -> {OUTPUTS_DIR / 'scorecard.csv'}")
    print(f"Saved combined predictions -> {OUTPUTS_DIR / 'pfinal_predictions.csv'}")


if __name__ == "__main__":
    main()

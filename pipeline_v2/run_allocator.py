#!/usr/bin/env python3
"""Runs the rule-based allocator with schema validation and business rules."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Models.rule_based import Zone, allocate_resources

from pipeline_v2 import schema
from pipeline_v2.business_rules import BusinessRuleError, RuleSet, enforce_rules
from pipeline_v2.logging_utils import configure_logging
from pipeline_v2.provenance import build_provenance, write_manifest
from pipeline_v2.zone_registry import load_zone_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--config", default="pipeline_v2/config.yaml")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _scenario_dict(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for entry in config.get("scenarios", []):
        if isinstance(entry, dict):
            name = entry.get("name")
            if not name:
                raise ValueError("Scenario entries require 'name'")
            result[name] = entry
        else:
            result[entry] = {"name": entry}
    return result


def _group_allocations(
    df: pd.DataFrame,
    bundle,
    total_units: int,
    mode: str,
    max_units_per_zone: Optional[int],
) -> List[Dict[str, Any]]:
    outputs: List[Dict[str, Any]] = []
    grouped = df.sort_values("timestamp").groupby("timestamp")
    for timestamp, group in grouped:
        zones = []
        for row in group.itertuples():
            zone_meta = bundle.zones.get(row.zone_id)
            zone_name = zone_meta.name if zone_meta else row.zone_id
            zones.append(
                Zone(
                    id=row.zone_id,
                    name=zone_name,
                    pf=float(row.pf_zone),
                    vulnerability=float(row.vulnerability),
                    is_critical_infra=bool(row.is_critical_infra),
                )
            )
        allocation = allocate_resources(
            zones,
            total_units=total_units,
            mode=mode,
            max_units_per_zone=max_units_per_zone,
        )
        alloc_map = {item["zone_id"]: item for item in allocation}
        for row in group.to_dict("records"):
            merged = {**row, **alloc_map[row["zone_id"]]}
            merged["timestamp"] = timestamp
            outputs.append(merged)
    return outputs


def main() -> None:
    args = parse_args()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    config_path = Path(args.config)
    config = load_config(config_path)
    scenarios = _scenario_dict(config)
    if args.scenario not in scenarios:
        raise KeyError(f"Scenario '{args.scenario}' missing in config")
    scenario_cfg = scenarios[args.scenario]

    standardized_root = Path(config.get("paths", {}).get("standardized", "Data/processed_v2"))
    results_root = Path(config.get("paths", {}).get("results", "Results/v2")) / args.scenario
    input_path = standardized_root / f"{args.scenario}_model_input.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Standardized input not found: {input_path}")

    logging.info("Loading standardized input %s", input_path)
    df = pd.read_csv(input_path)
    errors = schema.validate_dataframe("model_input", df, schema.MODEL_INPUT_SCHEMA)
    if errors:
        raise ValueError("; ".join(errors))

    zone_path = scenario_cfg.get("zone_config")
    if not zone_path:
        raise ValueError("Scenario config missing 'zone_config'")
    bundle = load_zone_file(args.scenario, Path(zone_path))
    total_units = int(scenario_cfg.get("total_units", config.get("total_units", 50)))
    max_units_per_zone_cfg = scenario_cfg.get("max_units_per_zone", config.get("max_units_per_zone"))
    min_critical_units = scenario_cfg.get("min_critical_units", config.get("min_critical_units", 1))
    mode = scenario_cfg.get("model_mode", config.get("model_mode", "proportional"))

    max_units_per_zone = int(max_units_per_zone_cfg) if max_units_per_zone_cfg else None
    if max_units_per_zone:
        max_capacity = max_units_per_zone * len(bundle.zones)
        effective_total_units = min(total_units, max_capacity)
        if effective_total_units < total_units:
            logging.warning(
                "Clamping total_units from %s to %s due to max_units_per_zone=%s and %s zones",
                total_units,
                effective_total_units,
                max_units_per_zone,
                len(bundle.zones),
            )
    else:
        effective_total_units = total_units

    rows = _group_allocations(
        df,
        bundle,
        total_units=effective_total_units,
        mode=mode,
        max_units_per_zone=max_units_per_zone,
    )
    if not rows:
        raise RuntimeError("Allocator produced no rows")
    output_df = pd.DataFrame(rows)

    errors = schema.validate_dataframe("allocation_output", output_df, schema.ALLOC_OUTPUT_SCHEMA)
    if errors:
        raise ValueError("; ".join(errors))

    rules = RuleSet(
        total_units=effective_total_units,
        min_critical_units=int(min_critical_units),
        max_units_per_zone=max_units_per_zone,
    )
    enforce_rules(output_df, bundle.zones.keys(), rules)

    results_root.mkdir(parents=True, exist_ok=True)
    ts_suffix = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    csv_path = results_root / f"allocations_{ts_suffix}.csv"
    json_path = results_root / f"summary_{ts_suffix}.json"
    output_df.to_csv(csv_path, index=False)

    summary = {
        "scenario": args.scenario,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "timestamps": output_df["timestamp"].nunique(),
        "total_rows": len(output_df),
        "mode": mode,
        "total_units": total_units,
    }
    json_path.write_text(yaml.safe_dump(summary, sort_keys=False), encoding="utf-8")
    logging.info("Wrote allocation csv=%s json=%s", csv_path, json_path)

    provenance = build_provenance(args.scenario, config_path, input_path, Path.cwd())
    manifest_path = results_root / f"provenance_{ts_suffix}.json"
    write_manifest(provenance, manifest_path)


if __name__ == "__main__":
    main()

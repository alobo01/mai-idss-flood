#!/usr/bin/env python3
"""Orchestrates the v2 pipeline with per-scenario error isolation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

from pipeline_v2.logging_utils import configure_logging

ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / "pipeline_v2" / "build_inputs.py"
ALLOC_SCRIPT = ROOT / "pipeline_v2" / "run_allocator.py"
CONFIG_DEFAULT = ROOT / "pipeline_v2" / "config.yaml"


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Pipeline v2 config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def scenario_names(config: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for entry in config.get("scenarios", []):
        if isinstance(entry, dict):
            name = entry.get("name")
            if not name:
                raise ValueError("Scenario entries require 'name'")
            names.append(name)
        else:
            names.append(entry)
    return names


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="Run only the specified scenario")
    parser.add_argument("--config", default=str(CONFIG_DEFAULT))
    parser.add_argument("--retries", type=int, default=1, help="Retries per stage on failure")
    args = parser.parse_args()

    configure_logging()

    config = load_config(Path(args.config))
    names = scenario_names(config)
    if not names:
        raise ValueError("No scenarios configured")

    targets = [args.scenario] if args.scenario else names
    unknown = set(targets) - set(names)
    if unknown:
        raise KeyError(f"Unknown scenario(s): {sorted(unknown)}")

    statuses: Dict[str, Dict[str, Any]] = {}

    for scenario in targets:
        scenario_status = {"scenario": scenario, "stages": [], "completed": False}
        for stage_name, script in (("build", BUILD_SCRIPT), ("allocate", ALLOC_SCRIPT)):
            attempt = 0
            success = False
            while attempt < max(1, args.retries) and not success:
                attempt += 1
                cmd = [sys.executable, str(script), "--scenario", scenario, "--config", args.config]
                result = _run(cmd)
                stage_record = {
                    "stage": stage_name,
                    "attempt": attempt,
                    "returncode": result.returncode,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                }
                if result.returncode == 0:
                    success = True
                else:
                    stage_record["error"] = f"Stage {stage_name} failed"
                scenario_status["stages"].append(stage_record)
                if not success and attempt < args.retries:
                    continue
            if not success:
                break
        scenario_status["completed"] = all(stage.get("returncode") == 0 for stage in scenario_status["stages"])
        statuses[scenario] = scenario_status

        results_root = Path(config.get("paths", {}).get("results", "Results/v2")) / scenario
        results_root.mkdir(parents=True, exist_ok=True)
        status_path = results_root / f"status_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        status_path.write_text(json.dumps(scenario_status, indent=2), encoding="utf-8")

    summary_path = Path(config.get("paths", {}).get("results", "Results/v2")) / "pipeline_status.json"
    summary_path.write_text(json.dumps(statuses, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

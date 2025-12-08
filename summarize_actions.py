"""Summarize rule-based allocations produced by pipeline_v3.

Reads one of the `pipeline_v3/outputs/rule_based/L*d_rule_based_allocations.csv`
files (or a user-provided CSV) and prints a human-readable action plan grouped
by timestamp. Only zones receiving non-zero units are listed unless `--verbose`
is supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

RESULTS_ROOT = Path("pipeline_v3/outputs/rule_based")
REQUIRED_COLUMNS = {
    "timestamp",
    "zone_name",
    "impact_level",
    "units_allocated",
    "vulnerability",
    "is_critical_infra",
    "allocation_mode",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize rule-based allocations for a lead horizon.")
    parser.add_argument("--lead", default="L1d", help="Lead horizon to summarize (e.g., L1d)")
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
        help="Optional explicit path to a rule-based allocations CSV file.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show zones even when zero units are allocated.")
    return parser.parse_args()


def resolve_csv_path(lead: str, override: Optional[str]) -> Path:
    if override:
        path = Path(override)
        if not path.exists():
            raise FileNotFoundError(f"Allocations file not found: {path}")
        return path

    sanitized = lead.strip()
    if not sanitized:
        raise ValueError("Lead argument cannot be empty")

    filename = f"{sanitized}_rule_based_allocations.csv"
    candidate = RESULTS_ROOT / filename
    if not candidate.exists():
        raise FileNotFoundError(
            f"Could not locate {filename} under {RESULTS_ROOT}. Run the pipeline first or supply --csv."
        )
    return candidate


def find_latest_file(base_dir: Path, prefix: str, suffix: str) -> Path:
    pattern = f"{prefix}*{suffix}"
    candidates = sorted(base_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No {prefix}*{suffix} files found in {base_dir}")
    return candidates[-1]


def load_allocations(csv_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Allocations file not found: {csv_path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Allocations file is empty: {csv_path}") from exc

    if "timestamp" not in df.columns:
        if "date" in df.columns:
            df = df.rename(columns={"date": "timestamp"})
        else:
            raise ValueError("Allocations file missing 'timestamp' or 'date' column.")

    if "zone_vulnerability" in df.columns and "vulnerability" not in df.columns:
        df = df.rename(columns={"zone_vulnerability": "vulnerability"})

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Allocations file missing required columns: {', '.join(sorted(missing))}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("One or more timestamps could not be parsed in allocations CSV.")
    return df.sort_values("timestamp")


def derive_summary_path(csv_path: Path) -> Path:
    suffix = csv_path.name.replace("allocations_", "")
    return csv_path.with_name(f"summary_{suffix}")


def read_summary_file(path: Path) -> Dict[str, Any]:
    text = path.read_text().strip()
    if not text:
        return {}

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except ModuleNotFoundError:
        pass
    except Exception:
        pass

    parsed: Dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip("'\"")
    return parsed


def format_units(value: Any) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if num.is_integer():
        return str(int(num))
    return f"{num:.2f}"


def summarize_timeline(df: pd.DataFrame, verbose: bool) -> None:
    print("Action Timeline:")
    grouped = df.groupby("timestamp", sort=True)
    for timestamp, group in grouped:
        display_group = group if verbose else group[group["units_allocated"] > 0]
        if display_group.empty:
            continue
        ts_str = timestamp.to_pydatetime().strftime("%Y-%m-%d %H:%M")
        print(f"[{ts_str}]")
        for row in display_group.itertuples(index=False):
            units = format_units(row.units_allocated)
            vuln = "NA"
            try:
                vuln = f"{float(row.vulnerability):.2f}"
            except (TypeError, ValueError):
                if row.vulnerability not in (None, ""):
                    vuln = str(row.vulnerability)
            critical_tag = " [critical infrastructure]" if bool(row.is_critical_infra) else ""
            print(
                f"  - {row.zone_name} ({row.impact_level}, mode={row.allocation_mode}, vulnerability={vuln}): "
                f"{units} units{critical_tag}"
            )
    print()


def summarize_metadata(summary_data: Dict[str, Any], df: pd.DataFrame, scenario: str) -> None:
    if not summary_data:
        return

    scenario_name = summary_data.get("scenario", scenario)
    generated_at = summary_data.get("generated_at", "unknown")
    total_rows = summary_data.get("total_rows", len(df))
    declared_units = summary_data.get("total_units")
    warnings = summary_data.get("warnings")
    if isinstance(warnings, str):
        warning_list = [warnings]
    elif isinstance(warnings, list):
        warning_list = [str(w) for w in warnings]
    elif warnings:
        warning_list = [str(warnings)]
    else:
        warning_list = []

    critical_zones = (
        df.loc[df["is_critical_infra"].astype(bool), "zone_name"].drop_duplicates().shape[0]
    )

    print("Summary Info:")
    print(f"  Scenario: {scenario_name}")
    print(f"  Generated at: {generated_at}")
    print(f"  Rows: {total_rows}")
    if declared_units is not None:
        print(f"  Total units allocated (declared target): {declared_units}")
    print(f"  Critical zones involved: {critical_zones}")
    if warning_list:
        print("  Warnings:")
        for warning in warning_list:
            print(f"    - {warning}")
    else:
        print("  Warnings: none recorded")
    print()


def main() -> None:
    args = parse_args()
    scenario_dir = RESULTS_ROOT / args.scenario
    if not scenario_dir.exists():
        sys.exit(f"Scenario directory not found: {scenario_dir}")

    try:
        allocations_path = find_latest_file(scenario_dir, "allocations_", ".csv")
    except FileNotFoundError as exc:
        sys.exit(str(exc))

    summary_path: Optional[Path] = None
    derived_summary = derive_summary_path(allocations_path)
    if derived_summary.exists():
        summary_path = derived_summary
    else:
        summary_candidates = list(scenario_dir.glob("summary_*.json"))
        if summary_candidates:
            summary_path = max(summary_candidates, key=lambda p: p.stat().st_mtime)

    try:
        df = load_allocations(allocations_path)
    except Exception as exc:
        sys.exit(str(exc))

    summary_data: Dict[str, Any] = {}
    if summary_path:
        try:
            summary_data = read_summary_file(summary_path)
        except Exception as exc:
            print(f"Warning: failed to read summary file ({exc})", file=sys.stderr)
            summary_data = {}

    print(f"Using allocations file: {allocations_path}")
    if summary_path:
        print(f"Using summary file: {summary_path}")
    print()

    summarize_metadata(summary_data, df, args.scenario)
    summarize_timeline(df, args.verbose)


if __name__ == "__main__":
    main()

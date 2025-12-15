"""Quick visualization utility for pipeline_v3 rule-based outputs.

Load one of the `pipeline_v3/outputs/rule_based/L*d_rule_based_allocations.csv`
files (or a user-provided CSV), filter it to a single zone, and plot predicted
severity versus deployed response units over time. Figures default to
`Results/plots/` unless a custom output path is supplied.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

RESULTS_ROOT = Path("pipeline_v3/outputs/rule_based")
PLOTS_ROOT = Path("./Results/plots")
DEFAULT_METRIC = "predicted_level"
VALID_METRICS = {
    "predicted_level": "Predicted river level",
    "global_pf": "Global probability of flood",
    "zone_pf": "Zone probability of flood",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot allocator predictions for a scenario/zone using the latest "
            "allocations CSV."
        )
    )
    parser.add_argument(
        "--lead",
        default="L1d",
        help="Lead horizon to load (e.g., L1d, L2d, L3d)",
    )
    parser.add_argument(
        "--zone",
        dest="zone_id",
        default=None,
        help="Zone identifier to plot (e.g., Z1N). Defaults to the first zone found.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
        help=(
            "Optional explicit path to a rule-based allocations CSV."
            " Overrides --lead when provided."
        ),
    )
    parser.add_argument(
        "--metric",
        choices=sorted(VALID_METRICS.keys()),
        default=DEFAULT_METRIC,
        help="Which severity metric to plot on the primary axis.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        help="Optional output path for the PNG figure.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the matplotlib window after saving the plot.",
    )
    return parser.parse_args()


def resolve_csv_path(lead: str, override: Optional[str]) -> Path:
    if override:
        path = Path(override)
        if not path.exists():
            raise FileNotFoundError(f"Specified CSV not found: {path}")
        return path

    sanitized = lead.strip()
    if not sanitized:
        raise ValueError("Lead argument cannot be empty")

    filename = f"{sanitized}_rule_based_allocations.csv"
    candidate = RESULTS_ROOT / filename
    if not candidate.exists():
        raise FileNotFoundError(
            f"Could not find {filename} under {RESULTS_ROOT}. Run pipeline_v3/main.py first or use --csv."
        )
    return candidate


def load_allocations(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "timestamp" not in df.columns:
        if "date" in df.columns:
            df = df.rename(columns={"date": "timestamp"})
        else:
            raise ValueError("Expected a 'timestamp' or 'date' column in allocations CSV.")

    if "predicted_level_ft" in df.columns and "predicted_level" not in df.columns:
        df = df.rename(columns={"predicted_level_ft": "predicted_level"})

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("One or more timestamps could not be parsed in the CSV.")
    return df


def resolve_zone(df: pd.DataFrame, requested_zone: Optional[str]) -> str:
    zones = df["zone_id"].unique()
    if requested_zone:
        if requested_zone not in zones:
            raise ValueError(
                f"Zone '{requested_zone}' not present in CSV. Available zones: {', '.join(zones)}"
            )
        return requested_zone
    return zones[0]


def make_output_path(args: argparse.Namespace, lead: str, zone_id: str) -> Path:
    if args.output_path:
        return Path(args.output_path)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    plots_dir = PLOTS_ROOT
    plots_dir.mkdir(parents=True, exist_ok=True)
    return plots_dir / f"{lead}_{zone_id}_allocations_{timestamp}.png"


def plot_zone_allocations(
    df: pd.DataFrame,
    zone_id: str,
    metric: str,
    output_path: Path,
    show_plot: bool,
) -> None:
    zone_df = df[df["zone_id"] == zone_id].sort_values("timestamp")
    if zone_df.empty:
        raise ValueError(f"Zone '{zone_id}' has no rows in the provided CSV.")

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(
        zone_df["timestamp"],
        zone_df[metric],
        color="tab:red",
        linewidth=2,
        label=VALID_METRICS[metric],
    )
    ax1.set_ylabel(VALID_METRICS[metric])
    ax1.set_xlabel("Timestamp")
    ax1.tick_params(axis="x", rotation=25)

    ax2 = ax1.twinx()
    ax2.bar(
        zone_df["timestamp"],
        zone_df["units_allocated"],
        width=0.03,
        color="tab:blue",
        alpha=0.4,
        label="Units allocated",
    )
    ax2.set_ylabel("Units allocated")

    title = f"Zone {zone_id} allocations vs. {VALID_METRICS[metric].lower()}"
    ax1.set_title(title)

    # Ensure readable date ticks.
    locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    fig.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left", bbox_to_anchor=(0.01, 0.99))

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    print(f"Saved plot to {output_path}")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)


def main() -> None:
    args = parse_args()
    csv_path = resolve_csv_path(args.lead, args.csv_path)
    df = load_allocations(csv_path)
    zone_id = resolve_zone(df, args.zone_id)
    output_path = make_output_path(args, args.lead, zone_id)
    plot_zone_allocations(df, zone_id, args.metric, output_path, args.show)


if __name__ == "__main__":
    main()
"""Business-rule enforcement for allocation outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd


@dataclass(frozen=True)
class RuleSet:
    total_units: int
    min_critical_units: int = 1
    max_units_per_zone: int | None = None
    depot_capacity: Dict[str, int] | None = None  # optional future use


class BusinessRuleError(RuntimeError):
    pass


def enforce_rules(df: pd.DataFrame, bundle_zones: Iterable[str], rules: RuleSet) -> None:
    if df.empty:
        raise BusinessRuleError("Allocation dataframe is empty")

    per_timestamp = df.groupby("timestamp")["units_allocated"].sum()
    if not (per_timestamp == rules.total_units).all():
        raise BusinessRuleError(
            "Total allocated units per timestamp do not match declared total_units"
        )

    critical = df[df["is_critical_infra"]]
    if not critical.empty:
        critical_sum = critical.groupby("timestamp")["units_allocated"].sum()
        if (critical_sum < rules.min_critical_units).any():
            raise BusinessRuleError(
                "Critical infrastructure received fewer units than min_critical_units"
            )

    if rules.max_units_per_zone is not None:
        zone_max = df.groupby("zone_id")["units_allocated"].max()
        if (zone_max > rules.max_units_per_zone).any():
            raise BusinessRuleError(
                "A zone exceeded max_units_per_zone"
            )

    missing_zones = set(bundle_zones) - set(df["zone_id"].unique())
    if missing_zones:
        raise BusinessRuleError(f"Missing allocations for zones: {sorted(missing_zones)}")

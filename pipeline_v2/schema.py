"""Declarative schemas and validation helpers for pipeline v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class FieldSpec:
    name: str
    dtype: type
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None


def _coerce(series: pd.Series, dtype: type) -> pd.Series:
    if dtype is float:
        return pd.to_numeric(series, errors="coerce")
    if dtype is int:
        return pd.to_numeric(series, errors="coerce", downcast="integer")
    if dtype is bool:
        if series.dtype == bool:
            return series
        lower = series.astype(str).str.lower()
        mapping = {"true": True, "false": False, "1": True, "0": False}
        return lower.map(mapping)
    if dtype is str:
        return series.astype(str)
    return series


def validate_dataframe(name: str, df: pd.DataFrame, schema: Iterable[FieldSpec]) -> List[str]:
    errors: List[str] = []
    for spec in schema:
        if spec.name not in df.columns:
            if spec.required:
                errors.append(f"{name}: missing column '{spec.name}'")
            continue
        series = _coerce(df[spec.name], spec.dtype)
        if series.isna().any() and spec.required:
            errors.append(f"{name}: column '{spec.name}' contains NaN after coercion")
            continue
        if spec.min_value is not None and (series < spec.min_value).any():
            errors.append(f"{name}: column '{spec.name}' below min {spec.min_value}")
        if spec.max_value is not None and (series > spec.max_value).any():
            errors.append(f"{name}: column '{spec.name}' above max {spec.max_value}")
    return errors


MODEL_INPUT_SCHEMA = [
    FieldSpec("timestamp", str),
    FieldSpec("scenario", str),
    FieldSpec("zone_id", str),
    FieldSpec("river_level_pred", float),
    FieldSpec("global_pf", float, min_value=0.0, max_value=1.0),
    FieldSpec("pf_zone", float, min_value=0.0, max_value=1.0),
    FieldSpec("vulnerability", float, min_value=0.0, max_value=1.0),
    FieldSpec("is_critical_infra", bool),
]


ALLOC_OUTPUT_SCHEMA = MODEL_INPUT_SCHEMA + [
    FieldSpec("impact_level", str),
    FieldSpec("allocation_mode", str),
    FieldSpec("units_allocated", int, min_value=0),
]

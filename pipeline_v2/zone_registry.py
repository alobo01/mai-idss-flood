"""Scenario-specific zone metadata loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml


@dataclass(frozen=True)
class ZoneProfile:
    id: str
    name: str
    vulnerability: float
    pf_weight: float
    is_critical_infra: bool
    hospital_count: int


@dataclass(frozen=True)
class ScenarioZoneBundle:
    scenario: str
    zones: Dict[str, ZoneProfile]


_DEFAULT_WEIGHTS = {
    "river_proximity": 0.35,
    "elevation_risk": 0.25,
    "pop_density": 0.25,
    "critical_infra": 0.15,
}


def _compute_vulnerability(weights: Dict[str, float], components: Dict[str, float]) -> float:
    score = 0.0
    for key, weight in weights.items():
        score += weight * float(components.get(key, 0.0))
    return min(1.0, max(0.0, round(score, 4)))


def load_zone_file(scenario: str, path: Path) -> ScenarioZoneBundle:
    if not path.exists():
        raise FileNotFoundError(f"Zone config for scenario '{scenario}' not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    weights = {**_DEFAULT_WEIGHTS, **(data.get("weights") or {})}
    zones_cfg = data.get("zones") or []
    zones: Dict[str, ZoneProfile] = {}
    for entry in zones_cfg:
        zone_id = entry.get("id")
        if not zone_id:
            raise ValueError(f"Zone entry missing 'id' in {path}")
        name = entry.get("name", zone_id)
        components = entry.get("components") or {}
        vulnerability = _compute_vulnerability(weights, components)
        pf_weight = float(entry.get("pf_weight", 1.0))
        hospital_count = int(entry.get("hospital_count", 0))
        is_critical = bool(entry.get("is_critical_infra", hospital_count > 0))
        zones[zone_id] = ZoneProfile(
            id=zone_id,
            name=name,
            vulnerability=vulnerability,
            pf_weight=pf_weight,
            is_critical_infra=is_critical,
            hospital_count=hospital_count,
        )
    if not zones:
        raise ValueError(f"No zones defined in {path}")
    return ScenarioZoneBundle(scenario=scenario, zones=zones)

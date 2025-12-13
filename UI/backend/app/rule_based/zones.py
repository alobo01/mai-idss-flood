from typing import Any, Dict, List

from ..schemas import Zone as ZoneModel


def _ensure_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def compute_vulnerability(attrs: Dict[str, Any]) -> float:
    return (
        0.35 * attrs.get("river_proximity", 0.0)
        + 0.25 * attrs.get("elevation_risk", 0.0)
        + 0.25 * attrs.get("pop_density", 0.0)
        + 0.15 * attrs.get("crit_infra_score", 0.0)
    )


def compute_pf_by_zone_from_global(rows: List[Dict[str, Any]], global_pf: float) -> Dict[str, float]:
    proximities = [
        _ensure_float(row.get("river_proximity"))
        for row in rows
        if row.get("river_proximity") is not None
    ]
    max_river = max(proximities) if proximities else 1.0

    pf_by_zone: Dict[str, float] = {}
    for row in rows:
        zone_id = row.get("zone_id")
        if not isinstance(zone_id, str):
            continue
        rp_norm = _ensure_float(row.get("river_proximity")) / max_river if max_river > 0 else 0.0
        weight = 0.5 + 0.5 * rp_norm
        pf_by_zone[zone_id] = min(1.0, global_pf * weight)

    return pf_by_zone


def build_zones_from_data(rows: List[Dict[str, Any]], pf_by_zone: Dict[str, float]) -> List[ZoneModel]:
    zones: List[ZoneModel] = []
    for row in rows:
        zone_id = row.get("zone_id")
        if not isinstance(zone_id, str):
            continue
        name = row.get("name") or zone_id

        attrs = {
            "river_proximity": _ensure_float(row.get("river_proximity")),
            "elevation_risk": _ensure_float(row.get("elevation_risk")),
            "pop_density": _ensure_float(row.get("pop_density")),
            "crit_infra_score": _ensure_float(row.get("crit_infra_score")),
        }
        vulnerability = compute_vulnerability(attrs)
        hospital_count = int(row.get("hospital_count") or 0)
        is_critical = bool(row.get("critical_infra") or hospital_count > 0)
        pf = pf_by_zone.get(zone_id, 0.0)

        zones.append(
            ZoneModel(
                id=zone_id,
                name=name,
                pf=pf,
                vulnerability=vulnerability,
                is_critical_infra=is_critical,
                hospital_count=hospital_count,
                river_proximity=attrs["river_proximity"],
                elevation_risk=attrs["elevation_risk"],
                pop_density=attrs["pop_density"],
                crit_infra_score=attrs["crit_infra_score"],
            )
        )

    return zones

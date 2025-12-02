from typing import List, Dict
from .rule_based import Zone
from .zone_config import ZONE_META, ZONE_ATTRIBUTES, ZONE_HOSPITAL_COUNT


def compute_vulnerability(attrs: Dict) -> float:
    return (
        0.35 * attrs["river_proximity"]
        + 0.25 * attrs["elevation_risk"]
        + 0.25 * attrs["pop_density"]
        + 0.15 * attrs["crit_infra_score"]
    )


def compute_pf_by_zone_from_global(global_pf: float) -> Dict[str, float]:
    pf_by_zone: Dict[str, float] = {}
    max_river = max(a["river_proximity"] for a in ZONE_ATTRIBUTES.values())

    for zone_id, attrs in ZONE_ATTRIBUTES.items():
        rp_norm = attrs["river_proximity"] / max_river
        weight = 0.5 + 0.5 * rp_norm
        pf_by_zone[zone_id] = min(1.0, global_pf * weight)

    return pf_by_zone


def build_zones_from_config(pf_by_zone: Dict[str, float]) -> List[Zone]:
    zones: List[Zone] = []

    for zone_id, meta in ZONE_META.items():
        attrs = ZONE_ATTRIBUTES[zone_id]
        vulnerability = compute_vulnerability(attrs)

        hospital_count = ZONE_HOSPITAL_COUNT.get(zone_id, 0)
        is_critical = hospital_count > 0

        pf = pf_by_zone.get(zone_id, 0.0)

        zones.append(
            Zone(
                id=zone_id,
                name=meta["name"],
                pf=pf,
                vulnerability=vulnerability,
                is_critical_infra=is_critical,
            )
        )

    return zones

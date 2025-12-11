from typing import Dict, List, Optional

from .zones import Zone

RESOURCE_TYPES = ["R1_UAV", "R2_ENGINEERING", "R3_PUMPS", "R4_RESCUE", "R5_EVAC"]


def _get_zone_attrs(zone: Zone) -> Dict[str, float]:
    return {
        "river_proximity": zone.river_proximity,
        "elevation_risk": zone.elevation_risk,
        "pop_density": zone.pop_density,
        "crit_infra_score": zone.crit_infra_score,
    }


# PROPORTIONAL MODE

def recommend_resources_proportional(zone: Zone, total_units: int, iz: float, sum_iz: float) -> Dict:
    units = 0 if sum_iz <= 0 else int(round(total_units * (iz / sum_iz)))
    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": classify_impact(zone.pf, zone.vulnerability),
        "allocation_mode": "PROPORTIONAL",
        "units_allocated": units,
    }


# CRISP MODE

def classify_impact(pf: float, vulnerability: float) -> str:
    iz = pf * vulnerability
    if iz < 0.3:
        return "NORMAL"
    if iz < 0.6:
        return "ADVISORY"
    if iz < 0.8:
        return "WARNING"
    return "CRITICAL"


def _crisp_fraction(impact: str, is_critical_infra: bool) -> float:
    if impact == "NORMAL":
        return 0.0
    if impact == "ADVISORY":
        return 0.1
    if impact == "WARNING":
        return 0.3
    return 0.6 if is_critical_infra else 0.5


def recommend_resources_crisp(zone: Zone, total_units: int) -> Dict:
    impact = classify_impact(zone.pf, zone.vulnerability)
    fraction = _crisp_fraction(impact, zone.is_critical_infra)
    units = max(0, int(total_units * fraction))
    if impact != "NORMAL" and units == 0:
        units = 1
    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": impact,
        "allocation_mode": "CRISP",
        "units_allocated": units,
    }


# FUZZY MODE

def _tri_mf(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def _fuzzy_fraction(iz: float, is_critical_infra: bool) -> float:
    mu_normal = _tri_mf(iz, 0.0, 0.0, 0.3)
    mu_advisory = _tri_mf(iz, 0.2, 0.45, 0.7)
    mu_warning = _tri_mf(iz, 0.4, 0.7, 0.9)
    mu_critical = _tri_mf(iz, 0.7, 1.0, 1.0)

    num = (
        mu_normal * 0.0
        + mu_advisory * 0.1
        + mu_warning * 0.3
        + mu_critical * 0.5
    )
    den = mu_normal + mu_advisory + mu_warning + mu_critical
    base = num / den if den > 0 else 0.0

    if is_critical_infra and iz >= 0.8:
        base += 0.1

    return max(0.0, min(base, 0.6))


def recommend_resources_fuzzy(zone: Zone, total_units: int) -> Dict:
    iz = zone.pf * zone.vulnerability
    units = int(round(total_units * _fuzzy_fraction(iz, zone.is_critical_infra)))
    if iz >= 0.3 and units == 0:
        units = 1
    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": classify_impact(zone.pf, zone.vulnerability),
        "allocation_mode": "FUZZY",
        "units_allocated": units,
    }


# RULE-BASED PRIORITIES

def rule_based_resource_scores(zone: Zone) -> Dict[str, float]:
    attrs = _get_zone_attrs(zone)
    river, elev, pop, ci = (
        attrs["river_proximity"],
        attrs["elevation_risk"],
        attrs["pop_density"],
        attrs["crit_infra_score"],
    )

    pf = zone.pf
    V = zone.vulnerability

    scores = {r: 0.0 for r in RESOURCE_TYPES}

    if river > 0.7 and pf > 0.4:
        scores["R1_UAV"] += 2
        scores["R2_ENGINEERING"] += 1

    if V > 0.7 and pf > 0.6:
        scores["R2_ENGINEERING"] += 3

    if elev > 0.6 and pf > 0.5:
        scores["R3_PUMPS"] += 3

    if pf > 0.7 or V > 0.75:
        scores["R4_RESCUE"] += 3

    if pop > 0.7 and pf > 0.5:
        scores["R5_EVAC"] += 3

    if ci > 0.6 or zone.is_critical_infra:
        scores["R2_ENGINEERING"] += 1
        scores["R5_EVAC"] += 1

    return scores


def resource_priority_list(zone: Zone) -> Dict:
    scores = rule_based_resource_scores(zone)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    ranked_nonzero = [k for k, v in ranked if v > 0]
    priority_index = 0.6 * zone.pf + 0.4 * zone.vulnerability

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "priority_index": priority_index,
        "resource_scores": scores,
        "resource_priority": ranked_nonzero,
    }


# DISPATCH

def build_dispatch_plan(
    zones: List[Zone],
    total_units: int,
    mode: str = "fuzzy",
    max_units_per_zone: Optional[int] = None,
) -> List[Dict]:
    numeric_alloc = allocate_resources(zones, total_units, mode, max_units_per_zone)
    priorities = {z.id: resource_priority_list(z) for z in zones}

    dispatch = []

    for alloc in numeric_alloc:
        zone_id = alloc["zone_id"]
        units = alloc["units_allocated"]
        pr = priorities.get(zone_id)

        resource_units = {r: 0 for r in RESOURCE_TYPES}

        if pr and pr["resource_priority"] and units > 0:
            p_list = pr["resource_priority"]
            i = 0
            for _ in range(units):
                resource_units[p_list[i % len(p_list)]] += 1
                i += 1

        dispatch.append(
            {
                **alloc,
                "priority_index": pr["priority_index"] if pr else None,
                "resource_priority": pr["resource_priority"] if pr else [],
                "resource_units": resource_units,
            }
        )

    return dispatch


def _rebalance_units(
    recs: List[Dict],
    diff: int,
    iz_map: Dict[str, float],
    max_units_per_zone: Optional[int] = None,
):
    if diff == 0:
        return

    ordered = sorted(recs, key=lambda r: iz_map.get(r["zone_id"], 0.0), reverse=True)
    direction = 1 if diff > 0 else -1
    remaining = abs(diff)

    while remaining > 0:
        changed = False
        for rec in ordered:
            if direction == -1 and rec["units_allocated"] == 0:
                continue
            if direction == 1 and max_units_per_zone is not None:
                if rec["units_allocated"] >= max_units_per_zone:
                    continue

            new_val = rec["units_allocated"] + direction
            if new_val < 0:
                continue

            rec["units_allocated"] = new_val
            remaining -= 1
            changed = True
            if remaining == 0:
                break

        if not changed:
            break


def allocate_resources(
    zones: List[Zone],
    total_units: int,
    mode: str = "crisp",
    max_units_per_zone: Optional[int] = None,
) -> List[Dict]:
    mode = mode.lower()
    if mode not in {"crisp", "fuzzy", "proportional"}:
        raise ValueError(f"Unknown mode {mode}")

    iz_map = {z.id: z.pf * z.vulnerability for z in zones}

    if mode == "proportional":
        sum_iz = sum(iz_map.values())
        recs = [
            recommend_resources_proportional(z, total_units, iz_map[z.id], sum_iz)
            for z in zones
        ]
    elif mode == "crisp":
        recs = [recommend_resources_crisp(z, total_units) for z in zones]
    else:
        recs = [recommend_resources_fuzzy(z, total_units) for z in zones]

    if mode in {"crisp", "fuzzy"}:
        total_requested = sum(r["units_allocated"] for r in recs)
        if total_requested > total_units:
            factor = total_units / total_requested
            for r in recs:
                if r["units_allocated"] > 0:
                    r["units_allocated"] = max(1, int(r["units_allocated"] * factor))

    if max_units_per_zone is not None:
        for r in recs:
            if r["units_allocated"] > max_units_per_zone:
                r["units_allocated"] = max_units_per_zone

    diff = total_units - sum(r["units_allocated"] for r in recs)
    _rebalance_units(recs, diff, iz_map, max_units_per_zone)

    return recs

from typing import Dict, List, Optional
import logging

from ..schemas import Zone as ZoneModel

logger = logging.getLogger(__name__)

# simpful import for fuzzy resource priorities
try:
    from simpful import (
        FuzzySystem,
        AutoTriangle,
        TriangleFuzzySet,
        LinguisticVariable,
    )
    _HAS_SIMPFUL = True
except Exception:
    _HAS_SIMPFUL = False

# Default fallback resource types (used if database is unavailable)
_DEFAULT_RESOURCE_TYPES = [
    "R1_UAV",
    "R2_ENGINEERING",
    "R3_PUMPS",
    "R4_RESCUE",
    "R5_EVAC",
    "R6_MEDICAL",
    "R7_CI",
]

# Cache for resource types loaded from database
_RESOURCE_TYPES_CACHE: Optional[List[str]] = None


def get_resource_types() -> List[str]:
    """Get resource types from database, with fallback to defaults."""
    global _RESOURCE_TYPES_CACHE
    
    if _RESOURCE_TYPES_CACHE is not None:
        return _RESOURCE_TYPES_CACHE
    
    try:
        from ..db import get_all_resource_types
        resource_data = get_all_resource_types()
        if resource_data:
            _RESOURCE_TYPES_CACHE = [r["resource_id"] for r in resource_data]
            return _RESOURCE_TYPES_CACHE
    except Exception:
        pass
    
    # Fallback to defaults
    _RESOURCE_TYPES_CACHE = _DEFAULT_RESOURCE_TYPES
    return _RESOURCE_TYPES_CACHE


# For backward compatibility
RESOURCE_TYPES = get_resource_types()


def _get_zone_attrs(zone: ZoneModel) -> Dict[str, float]:
    return {
        "river_proximity": zone.river_proximity,
        "elevation_risk": zone.elevation_risk,
        "pop_density": zone.pop_density,
        "crit_infra_score": zone.crit_infra_score,
    }


# PROPORTIONAL MODE

def recommend_resources_proportional(zone: ZoneModel, total_units: int, iz: float, sum_iz: float) -> Dict:
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
    if iz < 0.7:
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


def recommend_resources_crisp(zone: ZoneModel, total_units: int) -> Dict:
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


def recommend_resources_fuzzy(zone: ZoneModel, total_units: int) -> Dict:
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

_RESOURCE_FS: Optional["FuzzySystem"] = None  # type: ignore[name-defined]


def _build_resource_fuzzy_system() -> "FuzzySystem":  # type: ignore[name-defined]
    """
    Fuzzy system that maps zone + hazard attributes to a [0,1] priority for each resource.
    Inputs and outputs live in [0,1] and use low/medium/high fuzzy sets.
    """
    FS = FuzzySystem(show_banner=False)

    # ---- Input variables (all normalized in [0,1]) ----
    PF_LV = AutoTriangle(
        3,
        terms=["low", "medium", "high"],
        universe_of_discourse=[0.0, 1.0],
    )
    V_LV = AutoTriangle(
        3,
        terms=["low", "medium", "high"],
        universe_of_discourse=[0.0, 1.0],
    )
    RIVER_LV = AutoTriangle(
        3,
        terms=["low", "medium", "high"],
        universe_of_discourse=[0.0, 1.0],
    )
    ELEV_LV = AutoTriangle(
        3,
        terms=["low", "medium", "high"],
        universe_of_discourse=[0.0, 1.0],
    )
    POP_LV = AutoTriangle(
        3,
        terms=["low", "medium", "high"],
        universe_of_discourse=[0.0, 1.0],
    )
    CI_LV = AutoTriangle(
        3,
        terms=["low", "medium", "high"],
        universe_of_discourse=[0.0, 1.0],
    )

    FS.add_linguistic_variable("PF", PF_LV)
    FS.add_linguistic_variable("VULN", V_LV)
    FS.add_linguistic_variable("RIVER", RIVER_LV)
    FS.add_linguistic_variable("ELEV", ELEV_LV)
    FS.add_linguistic_variable("POP", POP_LV)
    FS.add_linguistic_variable("CI", CI_LV)

    # ---- Output variables: priority in [0,1] for each resource ----
    def _priority_lv() -> LinguisticVariable:
        return LinguisticVariable(
            [
                TriangleFuzzySet(0.0, 0.0, 0.4, term="low"),
                TriangleFuzzySet(0.0, 0.5, 1.0, term="medium"),
                TriangleFuzzySet(0.6, 1.0, 1.0, term="high"),
            ],
            universe_of_discourse=[0.0, 1.0],
        )

    FS.add_linguistic_variable("R1_UAV_PRI", _priority_lv())
    FS.add_linguistic_variable("R2_ENGINEERING_PRI", _priority_lv())
    FS.add_linguistic_variable("R3_PUMPS_PRI", _priority_lv())
    FS.add_linguistic_variable("R4_RESCUE_PRI", _priority_lv())
    FS.add_linguistic_variable("R5_EVAC_PRI", _priority_lv())
    FS.add_linguistic_variable("R6_MEDICAL_PRI", _priority_lv())
    FS.add_linguistic_variable("R7_CI_PRI", _priority_lv())

    # ---- Fuzzy rules (Mamdani style) ----
    rules = [
        # UAV & engineering when close to river and PF not low
        "IF (RIVER IS high) AND (PF IS medium) THEN (R1_UAV_PRI IS medium)",
        "IF (RIVER IS high) AND (PF IS medium) THEN (R2_ENGINEERING_PRI IS low)",
        "IF (RIVER IS high) AND (PF IS high) THEN (R1_UAV_PRI IS high)",
        "IF (RIVER IS high) AND (PF IS high) THEN (R2_ENGINEERING_PRI IS medium)",
        # Engineering for highly vulnerable + high PF
        "IF (VULN IS high) AND (PF IS high) THEN (R2_ENGINEERING_PRI IS high)",
        # Pumps for high elevation risk and non-low PF
        "IF (ELEV IS high) AND (PF IS medium) THEN (R3_PUMPS_PRI IS medium)",
        "IF (ELEV IS high) AND (PF IS high) THEN (R3_PUMPS_PRI IS high)",
        # Rescue for high PF OR high vulnerability
        "IF (PF IS high) OR (VULN IS high) THEN (R4_RESCUE_PRI IS high)",
        # Evacuation for high population and non-low PF
        "IF (POP IS high) AND (PF IS medium) THEN (R5_EVAC_PRI IS medium)",
        "IF (POP IS high) AND (PF IS high) THEN (R5_EVAC_PRI IS high)",
        # Critical infrastructure boosts engineering + evac
        "IF (CI IS high) THEN (R2_ENGINEERING_PRI IS medium)",
        "IF (CI IS high) THEN (R5_EVAC_PRI IS medium)",
        # Medical strike teams: high population and non-low PF
        "IF (POP IS high) AND (PF IS medium) THEN (R6_MEDICAL_PRI IS medium)",
        "IF (POP IS high) AND (PF IS high) THEN (R6_MEDICAL_PRI IS high)",
        "IF (CI IS high) AND (PF IS high) THEN (R6_MEDICAL_PRI IS high)",
        # CI protection / repair
        "IF (CI IS high) THEN (R7_CI_PRI IS medium)",
        "IF (CI IS high) AND (PF IS high) THEN (R7_CI_PRI IS high)",
    ]

    FS.add_rules(rules)
    return FS


if _HAS_SIMPFUL:
    _RESOURCE_FS = _build_resource_fuzzy_system()
else:
    _RESOURCE_FS = None


def fuzzy_resource_scores(zone: ZoneModel) -> Dict[str, float]:
    """
    Compute resource priority scores in [0,1] using the simpful fuzzy system.

    If simpful is not available, fall back to legacy crisp rules.
    """
    global _RESOURCE_FS

    if not _HAS_SIMPFUL or _RESOURCE_FS is None:
        return old_rule_based_resource_scores(zone)

    FS = _RESOURCE_FS

    attrs = _get_zone_attrs(zone)
    river = attrs["river_proximity"]
    elev = attrs["elevation_risk"]
    pop = attrs["pop_density"]
    ci = attrs["crit_infra_score"]

    # Clamp all inputs to [0,1]
    clamp = lambda x: max(0.0, min(1.0, float(x)))

    FS.set_variable("PF", clamp(zone.pf))
    FS.set_variable("VULN", clamp(zone.vulnerability))
    FS.set_variable("RIVER", clamp(river))
    FS.set_variable("ELEV", clamp(elev))
    FS.set_variable("POP", clamp(pop))
    FS.set_variable("CI", clamp(ci))

    out = FS.inference()

    # Map the fuzzy outputs to resource types
    scores = {
        "R1_UAV": float(out.get("R1_UAV_PRI", 0.0)),
        "R2_ENGINEERING": float(out.get("R2_ENGINEERING_PRI", 0.0)),
        "R3_PUMPS": float(out.get("R3_PUMPS_PRI", 0.0)),
        "R4_RESCUE": float(out.get("R4_RESCUE_PRI", 0.0)),
        "R5_EVAC": float(out.get("R5_EVAC_PRI", 0.0)),
        "R6_MEDICAL": float(out.get("R6_MEDICAL_PRI", 0.0)),
        "R7_CI": float(out.get("R7_CI_PRI", 0.0)),
    }

    return scores


def old_rule_based_resource_scores(zone: ZoneModel) -> Dict[str, float]:
    """Fallback crisp rule-based scoring if simpful is not available."""
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


def resource_priority_list(zone: ZoneModel, threshold: float = 0.05) -> Dict:
    """
    Return resource priorities for a zone.

    - Uses simpful fuzzy system if available.
    - Filters out resources with very low priority (<= threshold),
      so 'unnecessary' resources are not returned at all.
    """
    scores = fuzzy_resource_scores(zone)

    # Filter out resources with negligible priority
    filtered_scores = {k: v for k, v in scores.items() if v > threshold}

    # Sort by descending priority
    ranked = sorted(filtered_scores.items(), key=lambda kv: kv[1], reverse=True)
    ranked_resources = [k for k, _ in ranked]

    priority_index = 0.6 * zone.pf + 0.4 * zone.vulnerability

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "priority_index": priority_index,
        "resource_scores": filtered_scores,
        "resource_priority": ranked_resources,
    }


# DISPATCH

def build_dispatch_plan(
    zones: List[ZoneModel],
    total_units: int,
    mode: str = "fuzzy",
    max_units_per_zone: Optional[int] = None,
    use_optimizer: bool = False,
    resource_capacities: Optional[Dict[str, int]] = None,
) -> List[Dict]:
    
    # Get resource priorities for all zones
    priorities = {z.id: resource_priority_list(z) for z in zones}
    
    if use_optimizer and resource_capacities:
        # Use LP optimizer for fair allocation
        return _build_optimized_dispatch(zones, priorities, resource_capacities)
    else:
        # Use original heuristic allocation
        return _build_heuristic_dispatch(zones, total_units, mode, max_units_per_zone, priorities)


def _build_optimized_dispatch(
    zones: List[ZoneModel],
    priorities: Dict[str, Dict],
    resource_capacities: Dict[str, int]
) -> List[Dict]:
    """Build dispatch plan using LP optimizer for fair + necessity-aware allocation."""
    from .optimizer import optimize_fair_allocation

    # Prepare inputs for optimizer
    zone_list = [{"zone_id": z.id, "zone_name": z.name} for z in zones]

    resource_types = list(get_resource_types())

    # Total available capacity (across all resource types)
    total_available = int(sum(resource_capacities.values()))

    # Extract resource scores and build nominal allocations as fuzzy-estimated demand
    resource_scores: Dict[str, Dict[str, float]] = {}
    nominal_allocations: Dict[str, float] = {}

    for z in zones:
        zone_id = z.id
        pr = priorities.get(zone_id, {})

        # Zone-specific resource relevance / preference profile from fuzzy rules
        resource_scores[zone_id] = pr.get("resource_scores", {})

        # IMPORTANT: zone demand comes from fuzzy "units_allocated"
        # (this is the R_j used to scale the ideal bundle a_ij)
        fuzzy_need = recommend_resources_fuzzy(z, total_available)["units_allocated"]
        nominal_allocations[zone_id] = float(max(0, fuzzy_need))

    # If every zone has 0 need (e.g., NORMAL everywhere), return empty allocation
    if sum(nominal_allocations.values()) <= 0:
        dispatch = []
        for z in zones:
            dispatch.append({
                "zone_id": z.id,
                "zone_name": z.name,
                "impact_level": classify_impact(z.pf, z.vulnerability),
                "allocation_mode": "OPTIMIZED",
                "units_allocated": 0,
                "priority_index": priorities.get(z.id, {}).get("priority_index", 0.0),
                "resource_priority": priorities.get(z.id, {}).get("resource_priority", []),
                "resource_units": {r: 0 for r in resource_types},
                "resource_scores": priorities.get(z.id, {}).get("resource_scores", {}),
                "satisfaction_level": 0.0,
                "fairness_level": 0.0,
            })
        return dispatch

    # Use the same threshold as resource_priority_list default (keeps gating consistent)
    score_threshold = 0.05

    # Run optimization
    try:
        allocations, satisfaction_levels, fairness_level = optimize_fair_allocation(
            zone_list=zone_list,                 # if your function signature is positional, remove keywords
            resource_scores=resource_scores,
            nominal_allocations=nominal_allocations,
            capacities=resource_capacities,
            resource_types=resource_types,
            score_threshold=score_threshold,
        )

        logger.info(f"Optimization complete. Fairness level: {fairness_level:.3f}")

    except TypeError:
        # Backwards compatibility if optimize_fair_allocation is positional-only
        allocations, satisfaction_levels, fairness_level = optimize_fair_allocation(
            zone_list,
            resource_scores,
            nominal_allocations,
            resource_capacities,
            resource_types,
            score_threshold=score_threshold,
        )

    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        return _build_heuristic_dispatch(
            zones,
            sum(resource_capacities.values()),
            "fuzzy",
            None,
            priorities,
        )

    # Build dispatch response
    dispatch: List[Dict] = []

    for z in zones:
        zone_id = z.id
        pr = priorities.get(zone_id, {})
        zone_alloc = allocations.get(zone_id, {})

        # Round allocations to integers (LP is continuous)
        resource_units: Dict[str, int] = {}
        total_units_alloc = 0

        for resource_id in resource_types:
            amount = float(zone_alloc.get(resource_id, 0.0))
            rounded = int(round(amount))
            if rounded < 0:
                rounded = 0
            resource_units[resource_id] = rounded
            total_units_alloc += rounded

        satisfaction = float(satisfaction_levels.get(zone_id, 0.0))

        dispatch.append({
            "zone_id": zone_id,
            "zone_name": z.name,
            "impact_level": classify_impact(z.pf, z.vulnerability),
            "allocation_mode": "OPTIMIZED",
            "units_allocated": total_units_alloc,
            "priority_index": pr.get("priority_index", 0.0),
            "resource_priority": pr.get("resource_priority", []),
            "resource_units": resource_units,
            "resource_scores": pr.get("resource_scores", {}),
            "satisfaction_level": round(satisfaction, 3),
            "fairness_level": round(float(fairness_level), 3),
        })

    return dispatch


def _build_heuristic_dispatch(
    zones: List[ZoneModel],
    total_units: int,
    mode: str,
    max_units_per_zone: Optional[int],
    priorities: Dict[str, Dict]
) -> List[Dict]:
    """Build dispatch plan using original heuristic allocation."""
    numeric_alloc = allocate_resources(zones, total_units, mode, max_units_per_zone)
    
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
                "resource_scores": pr.get("resource_scores", {}) if pr else {},
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
    zones: List[ZoneModel],
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

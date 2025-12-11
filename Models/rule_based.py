# pylint: disable=astroid-error
"""Rule-based, fuzzy, and crisp allocation of flood response resources.

This file merges:
- The official main-branch allocation API (crisp, fuzzy, proportional)
- Your knowledge-based multi-resource scoring system
- A final dispatch planner that distributes allocated units across resource types
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

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


# ---------------------------------------------------------------------------
# Optional import for extended zone attributes (safe fallback)
# ---------------------------------------------------------------------------
try:
    from Models.zone_config import ZONE_ATTRIBUTES
except Exception:
    ZONE_ATTRIBUTES = {}  # allows running without extended config


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Zone:
    id: str
    name: str
    pf: float
    vulnerability: float
    is_critical_infra: bool


# ---------------------------------------------------------------------------
# Resource type definitions (your extension)
# ---------------------------------------------------------------------------

RESOURCE_TYPES = [
    "R1_UAV",
    "R2_ENGINEERING",
    "R3_PUMPS",
    "R4_RESCUE",
    "R5_EVAC",
    "R6_MEDICAL",
    "R7_CI",
]




def _get_zone_attrs(zone: Zone) -> Dict[str, float]:
    """Fetch additional zone attributes from ZONE_ATTRIBUTES."""
    attrs = ZONE_ATTRIBUTES.get(zone.id, {})
    return {
        "river_proximity": attrs.get("river_proximity", 0.0),
        "elevation_risk": attrs.get("elevation_risk", 0.0),
        "pop_density": attrs.get("pop_density", 0.0),
        "crit_infra_score": attrs.get("crit_infra_score", 0.0),
    }


# ---------------------------------------------------------------------------
# PROPORTIONAL
# ---------------------------------------------------------------------------

def recommend_resources_proportional(zone: Zone, total_units: int, iz: float, sum_iz: float) -> Dict:
    if sum_iz <= 0:
        units = 0
    else:
        units = int(round(total_units * (iz / sum_iz)))

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": classify_impact(zone.pf, zone.vulnerability),
        "allocation_mode": "PROPORTIONAL",
        "units_allocated": units,
    }


# ---------------------------------------------------------------------------
# CRISP CLASSIFICATION
# ---------------------------------------------------------------------------

def classify_impact(pf: float, vulnerability: float) -> str:
    iz = pf * vulnerability
    if iz < 0.3:
        return "NORMAL"
    elif iz < 0.6:
        return "ADVISORY"
    elif iz < 0.8:
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


# ---------------------------------------------------------------------------
# FUZZY LOGIC
# ---------------------------------------------------------------------------

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
        mu_normal * 0.0 +
        mu_advisory * 0.1 +
        mu_warning * 0.3 +
        mu_critical * 0.5
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

# ---------------------------------------------------------------------------
# FUZZY MULTI-RESOURCE PRIORITIES USING SIMPFUL
# ---------------------------------------------------------------------------

_RESOURCE_FS: Optional["FuzzySystem"] = None  # type: ignore[name-defined]


def _build_resource_fuzzy_system() -> "FuzzySystem":  # type: ignore[name-defined]
    """
    Fuzzy system that maps zone + hazard attributes to a [0,1] priority for each resource.
    Inputs and outputs live in [0,1] and use low/medium/high fuzzy sets.
    """
    FS = FuzzySystem(show_banner=False)


    # ---- Input variables (all normalized in [0,1]) ----
    # PF: flood probability / intensity
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
        # Medical strike teams: high population and non-low PF (health surge),
        # plus extra emphasis if CI (e.g. hospitals) is high.
        "IF (POP IS high) AND (PF IS medium) THEN (R6_MEDICAL_PRI IS medium)",
        "IF (POP IS high) AND (PF IS high) THEN (R6_MEDICAL_PRI IS high)",
        "IF (CI IS high) AND (PF IS high) THEN (R6_MEDICAL_PRI IS high)",

        # CI protection / repair: triggered mainly by high CI exposure, more strongly
        # when flood risk is high.
        "IF (CI IS high) THEN (R7_CI_PRI IS medium)",
        "IF (CI IS high) AND (PF IS high) THEN (R7_CI_PRI IS high)",
     ]


    FS.add_rules(rules)
    return FS


if _HAS_SIMPFUL:
    _RESOURCE_FS = _build_resource_fuzzy_system()
else:
    _RESOURCE_FS = None


def fuzzy_resource_scores(zone: Zone) -> Dict[str, float]:
    """
    Compute resource priority scores in [0,1] using the simpful fuzzy system.

    If simpful is not available, fall back to the legacy crisp rules.
    """
    global _RESOURCE_FS

    if not _HAS_SIMPFUL or _RESOURCE_FS is None:
        # Fallback: maintain behaviour if the library is missing.
        return old_rule_based_resource_scores(zone)

    FS = _RESOURCE_FS

    attrs = _get_zone_attrs(zone)
    river = attrs["river_proximity"]
    elev = attrs["elevation_risk"]
    pop = attrs["pop_density"]
    ci = attrs["crit_infra_score"]

    # Clamp all inputs to [0,1] to match the universe_of_discourse
    clamp = lambda x: max(0.0, min(1.0, float(x)))

    FS.set_variable("PF", clamp(zone.pf))
    FS.set_variable("VULN", clamp(zone.vulnerability))
    FS.set_variable("RIVER", clamp(river))
    FS.set_variable("ELEV", clamp(elev))
    FS.set_variable("POP", clamp(pop))
    FS.set_variable("CI", clamp(ci))

    out = FS.inference()

    # Map the fuzzy outputs to your resource types (crisp scores in [0,1])
    scores = {
    "R1_UAV":         float(out.get("R1_UAV_PRI", 0.0)),
    "R2_ENGINEERING": float(out.get("R2_ENGINEERING_PRI", 0.0)),
    "R3_PUMPS":       float(out.get("R3_PUMPS_PRI", 0.0)),
    "R4_RESCUE":      float(out.get("R4_RESCUE_PRI", 0.0)),
    "R5_EVAC":        float(out.get("R5_EVAC_PRI", 0.0)),
    "R6_MEDICAL":     float(out.get("R6_MEDICAL_PRI", 0.0)),
    "R7_CI":          float(out.get("R7_CI_PRI", 0.0)),
    }


    return scores

# ---------------------------------------------------------------------------
# OLD JUST IF SIMPFUL DOESNT WORK
# ---------------------------------------------------------------------------

def old_rule_based_resource_scores(zone: Zone) -> Dict[str, float]:
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


def resource_priority_list(zone: Zone, threshold: float = 0.05) -> Dict:
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

    # You already had this combined index, keep it (Antonio only wants priority)
    priority_index = 0.6 * zone.pf + 0.4 * zone.vulnerability

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "priority_index": priority_index,
        "resource_scores": filtered_scores,
        "resource_priority": ranked_resources,
    }


# ---------------------------------------------------------------------------
# FINAL DISPATCH PLAN
# ---------------------------------------------------------------------------

def build_dispatch_plan(zones: List[Zone], total_units: int, mode: str = "fuzzy",
                        max_units_per_zone: Optional[int] = None) -> List[Dict]:

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

        dispatch.append({
            **alloc,
            "priority_index": pr["priority_index"] if pr else None,
            "resource_priority": pr["resource_priority"] if pr else [],
            "resource_units": resource_units,
        })

    return dispatch


# ---------------------------------------------------------------------------
# REBALANCING + PUBLIC allocate_resources API (unchanged from main)
# ---------------------------------------------------------------------------

def _rebalance_units(recs: List[Dict], diff: int, iz_map: Dict[str, float],
                     max_units_per_zone: Optional[int] = None):

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


def allocate_resources(zones: List[Zone], total_units: int, mode: str = "crisp",
                       max_units_per_zone: Optional[int] = None) -> List[Dict]:

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

    # Normalization step (matches main)
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

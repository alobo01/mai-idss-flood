# pylint: disable=astroid-error
"""Rule-based and fuzzy-logic allocation of flood response resources.

This module defines a Zone dataclass, classifies impact levels based on
predicted flood probability and vulnerability, and recommends resource
allocation across zones.

Two allocation modes are supported:
- CRISP: step-wise thresholds (NORMAL / ADVISORY / WARNING / CRITICAL)
- FUZZY: fuzzy combination of the same linguistic levels based on an
  impact score Iz = pf * vulnerability.
"""

from dataclasses import dataclass
from typing import List, Dict


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Zone:
    """Represents a spatial zone in the flood IDSS.

    Attributes:
        id: Zone identifier (e.g. "Z1").
        name: Human-readable name (e.g. "Riverfront High-Risk").
        pf: Predicted flood probability in [0, 1].
        vulnerability: Composite index in [0, 1] encoding river proximity,
            elevation risk, population density, hospital/critical infra, etc.
        is_critical_infra: True if the zone contains critical infrastructure
            (e.g. major hospitals, wastewater plants, power substations).
    """
    id: str
    name: str
    pf: float
    vulnerability: float
    is_critical_infra: bool

# ---------------------------------------------------------------------------
# proportional model
# ---------------------------------------------------------------------------
def recommend_resources_proportional(
    zone: Zone,
    total_units: int,
    iz: float,
    sum_iz: float,
) -> Dict:
    """Allocate resources strictly proportional to impact Iz / sum(I_all)."""
    if sum_iz <= 0:
        units = 0
    else:
        raw_units = total_units * (iz / sum_iz)
        units = int(round(raw_units))

    impact = classify_impact(zone.pf, zone.vulnerability)

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": impact,
        "allocation_mode": "PROPORTIONAL",
        "units_allocated": units,
    }

# ---------------------------------------------------------------------------
# CRISP IMPACT CLASSIFICATION
# ---------------------------------------------------------------------------


def classify_impact(pf: float, vulnerability: float) -> str:
    """Classify impact level based on predicted flood probability and vulnerability.

    Impact score:
        Iz = pf * vulnerability

    Returns one of:
        "NORMAL", "ADVISORY", "WARNING", "CRITICAL".
    """
    iz = pf * vulnerability

    if iz < 0.3:
        return "NORMAL"
    elif iz < 0.6:
        return "ADVISORY"
    elif iz < 0.8:
        return "WARNING"
    else:
        return "CRITICAL"


def _crisp_fraction(impact: str, is_critical_infra: bool) -> float:
    """Resource fraction according to the original crisp rules."""
    if impact == "NORMAL":
        return 0.0
    if impact == "ADVISORY":
        return 0.1
    if impact == "WARNING":
        return 0.3
    # CRITICAL
    return 0.6 if is_critical_infra else 0.5


def recommend_resources_crisp(zone: Zone, total_units: int) -> Dict:
    """Recommend how many units to allocate to a single zone (crisp rules)."""
    impact = classify_impact(zone.pf, zone.vulnerability)
    fraction = _crisp_fraction(impact, zone.is_critical_infra)
    units = max(0, int(total_units * fraction))

    # Ensure at least 1 unit if we decided to allocate something
    if impact in {"ADVISORY", "WARNING", "CRITICAL"} and units == 0:
        units = 1

    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": impact,
        "allocation_mode": "CRISP",
        "units_allocated": units,
    }


# ---------------------------------------------------------------------------
# FUZZY LOGIC EXTENSION
# ---------------------------------------------------------------------------


def _tri_mf(x: float, a: float, b: float, c: float) -> float:
    """Triangular membership function mu(x; a, b, c)."""
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    # x > b
    return (c - x) / (c - b)


def _fuzzy_fraction(iz: float, is_critical_infra: bool) -> float:
    """Compute resource fraction using fuzzy membership over impact levels.

    - Input: impact score iz in [0, 1]
    - Output: resource fraction in [0, ~0.6]

    Linguistic impact levels are defined over iz with overlapping triangular
    membership functions. Each level has a "typical" resource fraction.
    A weighted average over these consequents is used for defuzzification.
    """
    # 1) Membership degrees for linguistic levels over Iz
    mu_normal = _tri_mf(iz, 0.0, 0.0, 0.3)
    mu_advisory = _tri_mf(iz, 0.2, 0.45, 0.7)
    mu_warning = _tri_mf(iz, 0.4, 0.7, 0.9)
    mu_critical = _tri_mf(iz, 0.7, 1.0, 1.0)

    # 2) "Typical" resource fractions per level (aligned with crisp rules)
    frac_normal = 0.0
    frac_advisory = 0.1
    frac_warning = 0.3
    frac_critical = 0.5  # base for critical

    # 3) Weighted average over consequents
    num = (
        mu_normal * frac_normal
        + mu_advisory * frac_advisory
        + mu_warning * frac_warning
        + mu_critical * frac_critical
    )
    den = mu_normal + mu_advisory + mu_warning + mu_critical

    if den == 0:
        base_fraction = 0.0
    else:
        base_fraction = num / den

    # 4) Critical infrastructure bonus at high impact
    if is_critical_infra and iz >= 0.8:
        base_fraction += 0.1

    # Cap between 0 and 0.6 to stay comparable with crisp logic
    return max(0.0, min(base_fraction, 0.6))


def recommend_resources_fuzzy(zone: Zone, total_units: int) -> Dict:
    """Recommend how many units to allocate using fuzzy rules.

    Uses fuzzy membership over impact score Iz, then defuzzifies to a
    single resource fraction.
    """
    iz = zone.pf * zone.vulnerability
    fraction = _fuzzy_fraction(iz, zone.is_critical_infra)
    units = int(round(total_units * fraction))

    # Ensure at least 1 unit if impact is non-trivial
    if iz >= 0.3 and units == 0:
        units = 1

    impact = classify_impact(zone.pf, zone.vulnerability)
    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "impact_level": impact,
        "allocation_mode": "FUZZY",
        "units_allocated": units,
    }


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


def allocate_resources(
    zones: List[Zone],
    total_units: int,
    mode: str = "crisp",
) -> List[Dict]:
    mode = mode.lower()
    if mode not in {"crisp", "fuzzy", "proportional"}:
        raise ValueError(f"Unknown allocation mode: {mode}")

    if mode == "proportional":
        # Compute Iz and sum_iz once
        iz_by_zone = {z.id: z.pf * z.vulnerability for z in zones}
        sum_iz = sum(iz_by_zone.values())

        recommendations = [
            recommend_resources_proportional(z, total_units, iz_by_zone[z.id], sum_iz)
            for z in zones
        ]

        # Optional: small correction so we don't exceed total_units by rounding
        total_alloc = sum(r["units_allocated"] for r in recommendations)
        diff = total_units - total_alloc
        if diff != 0:
            # Adjust by giving/removing 1 unit to some zones, e.g. by highest Iz
            # For simplicity you can skip this, or implement a refinement later.
            pass

    elif mode == "crisp":
        recommendations = [
            recommend_resources_crisp(zone, total_units) for zone in zones
        ]
    else:  # fuzzy
        recommendations = [
            recommend_resources_fuzzy(zone, total_units) for zone in zones
        ]

    # Keep your normalization for CRISP/FUZZY only
    if mode in {"crisp", "fuzzy"}:
        total_requested = sum(r["units_allocated"] for r in recommendations)
        if total_requested > total_units and total_requested > 0:
            factor = total_units / total_requested
            for r in recommendations:
                if r["units_allocated"] > 0:
                    r["units_allocated"] = max(
                        1, int(r["units_allocated"] * factor)
                    )

    return recommendations



# ---------------------------------------------------------------------------
# Simple manual test with river-based St. Louis zones
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example zones consistent with the St. Louis river logic:
    # Z1: Riverfront High-Risk (closest to Mississippi, low elevation)
    # Z2: Near-River Urban / Medical Core
    # Z3: Inland South Residential
    # Z4: Inland North / Outer Residential

    zones = [
        Zone(
            id="Z1",
            name="Riverfront High-Risk",
            pf=0.85,             # high flood probability from gauge model
            vulnerability=0.9,   # very exposed (river + low elevation + dense)
            is_critical_infra=True,  # hospitals and key infra present
        ),
        Zone(
            id="Z2",
            name="Near-River Medical Core",
            pf=0.7,
            vulnerability=0.85,  # high pop + hospitals, slightly higher ground
            is_critical_infra=True,
        ),
        Zone(
            id="Z3",
            name="Inland South Residential",
            pf=0.4,
            vulnerability=0.5,   # further from river, mainly residential
            is_critical_infra=False,
        ),
        Zone(
            id="Z4",
            name="Inland North Residential",
            pf=0.5,
            vulnerability=0.6,   # some exposure + one emergency hospital
            is_critical_infra=True,
        ),
    ]

    print("=== CRISP ALLOCATION ===")
    for r in allocate_resources(zones, total_units=10, mode="crisp"):
        print(r)

    print("\n=== FUZZY ALLOCATION ===")
    for r in allocate_resources(zones, total_units=10, mode="fuzzy"):
        print(r)

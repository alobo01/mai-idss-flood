"""Local zone metadata reused by the backend rule engine."""

ZONE_META = {
    "Z1N": {"name": "North Riverfront Floodplain"},
    "Z1S": {"name": "South Riverfront Floodplain"},
    "Z2": {"name": "Central Business & Medical Core"},
    "Z3": {"name": "Inland South Residential Plateau"},
    "Z4": {"name": "Inland North Residential Plateau"},
    "ZC": {"name": "Central / Special ZIPs"},
}

ZONE_ATTRIBUTES = {
    "Z1N": {
        "river_proximity": 0.98,
        "elevation_risk": 0.95,
        "pop_density": 0.75,
        "crit_infra_score": 0.4,
    },
    "Z1S": {
        "river_proximity": 0.95,
        "elevation_risk": 0.9,
        "pop_density": 0.8,
        "crit_infra_score": 0.5,
    },
    "Z2": {
        "river_proximity": 0.75,
        "elevation_risk": 0.7,
        "pop_density": 0.9,
        "crit_infra_score": 0.9,
    },
    "Z3": {
        "river_proximity": 0.4,
        "elevation_risk": 0.45,
        "pop_density": 0.7,
        "crit_infra_score": 0.35,
    },
    "Z4": {
        "river_proximity": 0.45,
        "elevation_risk": 0.5,
        "pop_density": 0.75,
        "crit_infra_score": 0.4,
    },
    "ZC": {
        "river_proximity": 0.7,
        "elevation_risk": 0.7,
        "pop_density": 0.1,
        "crit_infra_score": 0.2,
    },
}

ZONE_HOSPITAL_COUNT = {
    "Z1N": 1,
    "Z1S": 2,
    "Z2": 6,
    "Z3": 0,
    "Z4": 0,
    "ZC": 0,
}

ZONE_CRITICAL_INFRA = {zone: count > 0 for zone, count in ZONE_HOSPITAL_COUNT.items()}

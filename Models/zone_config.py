# zone_config.py

# ---------------------------------------------------------------------------
# ZIP → ZONE mapping
# Covers all St. Louis City ZIP codes + a few near-city north zips (63133, 63136, 63137)
# ---------------------------------------------------------------------------

ZIP_TO_ZONE = {
    # Z1N – North Riverfront Floodplain
    "63102": "Z1N",
    "63101": "Z1N",
    "63103": "Z1N",
    "63106": "Z1N",
    "63107": "Z1N",
    "63147": "Z1N",
    "63155": "Z1N",
    "63156": "Z1N",
    "63157": "Z1N",
    "63158": "Z1N",
    "63163": "Z1N",
    "63166": "Z1N",
    "63169": "Z1N",
    "63177": "Z1N",
    "63178": "Z1N",
    "63179": "Z1N",
    "63188": "Z1N",

    # Z1S – South Riverfront Floodplain
    "63104": "Z1S",
    "63111": "Z1S",
    "63118": "Z1S",

    # Z2 – Central Business & Medical Core
    "63108": "Z2",
    "63110": "Z2",
    "63112": "Z2",

    # Z3 – Inland South Residential Plateau
    "63109": "Z3",
    "63116": "Z3",
    "63139": "Z3",

    # Z4 – Inland North Residential Plateau
    "63113": "Z4",
    "63115": "Z4",
    "63120": "Z4",
}


# ---------------------------------------------------------------------------
# Zone metadata
# ---------------------------------------------------------------------------

ZONE_META = {
    "Z1N": {"name": "North Riverfront Floodplain"},
    "Z1S": {"name": "South Riverfront Floodplain"},
    "Z2":  {"name": "Central Business & Medical Core"},
    "Z3":  {"name": "Inland South Residential Plateau"},
    "Z4":  {"name": "Inland North Residential Plateau"},
}


# ---------------------------------------------------------------------------
# Zone-level vulnerability attributes
# (same structure as you already had)
# ---------------------------------------------------------------------------

ZONE_ATTRIBUTES = {
    "Z1N": {
        "river_proximity": 0.98,
        "elevation_risk": 0.95,
        "pop_density": 0.75,
        "crit_infra_score": 0.4,
    },
    "Z1S": {
        "river_proximity": 0.95,
        "elevation_risk": 0.90,
        "pop_density": 0.80,
        "crit_infra_score": 0.5,
    },
    "Z2": {
        "river_proximity": 0.75,
        "elevation_risk": 0.70,
        "pop_density": 0.90,
        "crit_infra_score": 0.9,  # big hospital cluster
    },
    "Z3": {
        "river_proximity": 0.40,
        "elevation_risk": 0.45,
        "pop_density": 0.70,
        "crit_infra_score": 0.35,
    },
    "Z4": {
        "river_proximity": 0.45,
        "elevation_risk": 0.50,
        "pop_density": 0.75,
        "crit_infra_score": 0.4,
    },
}

# ---------------------------------------------------------------------------
# Hospital counts per zone (derived from your CSV + ZIP_TO_ZONE)
# ---------------------------------------------------------------------------
# City/near-city hospitals in CSV:
#   63104 (2), 63106 (1)  → Z1
#   63110 (5), 63112 (1)  → Z2
#   63133 (1), 63136 (1)  → Z4
# Z3 has no hospitals in the dataset.

ZONE_HOSPITAL_COUNT = {
    "Z1N": 1,
    "Z1S": 2,
    "Z2":  6,
    "Z3":  0,
    "Z4":  0,
}

ZONE_CRITICAL_INFRA = {
    zone_id: (count > 0) for zone_id, count in ZONE_HOSPITAL_COUNT.items()
}

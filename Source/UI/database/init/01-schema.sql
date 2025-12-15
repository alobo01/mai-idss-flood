-- Database initialization for flood prediction data
-- Tables: raw_data, predictions, zones, zip_zones, zip_geojson

-- Raw hydrologic inputs
CREATE TABLE IF NOT EXISTS raw_data (
    date DATE PRIMARY KEY,
    daily_precip DOUBLE PRECISION,
    daily_temp_avg DOUBLE PRECISION,
    daily_snowfall DOUBLE PRECISION,
    daily_humidity DOUBLE PRECISION,
    daily_wind DOUBLE PRECISION,
    soil_deep_30d DOUBLE PRECISION,
    target_level_max DOUBLE PRECISION,
    hermann_level DOUBLE PRECISION,
    grafton_level DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model predictions
CREATE TABLE IF NOT EXISTS predictions (
    date DATE NOT NULL,
    predicted_level DOUBLE PRECISION,
    flood_probability DOUBLE PRECISION CHECK (flood_probability >= 0 AND flood_probability <= 1),
    days_ahead INTEGER CHECK (days_ahead >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT predictions_pkey PRIMARY KEY (date, days_ahead)
);

-- Zone metadata
CREATE TABLE IF NOT EXISTS zones (
    zone_id VARCHAR(4) PRIMARY KEY,
    name TEXT NOT NULL,
    river_proximity DECIMAL(3,2) NOT NULL,
    elevation_risk DECIMAL(3,2) NOT NULL,
    pop_density DECIMAL(3,2) NOT NULL,
    crit_infra_score DECIMAL(3,2) NOT NULL,
    hospital_count INTEGER NOT NULL,
    critical_infra BOOLEAN NOT NULL
);

-- ZIP to zone mapping
CREATE TABLE IF NOT EXISTS zip_zones (
    zip_code CHAR(5) PRIMARY KEY,
    zone_id VARCHAR(4) NOT NULL REFERENCES zones(zone_id)
);

-- ZIP GeoJSON storage (unpopulated by default)
CREATE TABLE IF NOT EXISTS zip_geojson (
    zip_code CHAR(5) PRIMARY KEY,
    geojson JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resource types catalog
CREATE TABLE IF NOT EXISTS resource_types (
    resource_id VARCHAR(20) PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed zones
INSERT INTO zones (zone_id, name, river_proximity, elevation_risk, pop_density, crit_infra_score, hospital_count, critical_infra) VALUES
  ('Z1N', 'North Riverfront Floodplain',         0.98, 0.95, 0.75, 0.40, 1, TRUE),
  ('Z1S', 'South Riverfront Floodplain',         0.95, 0.90, 0.80, 0.50, 2, TRUE),
  ('Z2',  'Central Business & Medical Core',     0.75, 0.70, 0.90, 0.90, 6, TRUE),
  ('Z3',  'Inland South Residential Plateau',    0.40, 0.45, 0.70, 0.35, 0, FALSE),
  ('Z4',  'Inland North Residential Plateau',    0.45, 0.50, 0.75, 0.40, 0, FALSE)
ON CONFLICT (zone_id) DO NOTHING;

-- Seed ZIP mappings
INSERT INTO zip_zones (zip_code, zone_id) VALUES
  ('63102', 'Z1N'),
  ('63101', 'Z1N'),
  ('63103', 'Z1N'),
  ('63106', 'Z1N'),
  ('63107', 'Z1N'),
  ('63147', 'Z1N'),
  ('63155', 'Z1N'),
  ('63156', 'Z1N'),
  ('63157', 'Z1N'),
  ('63158', 'Z1N'),
  ('63163', 'Z1N'),
  ('63166', 'Z1N'),
  ('63169', 'Z1N'),
  ('63177', 'Z1N'),
  ('63178', 'Z1N'),
  ('63179', 'Z1N'),
  ('63188', 'Z1N'),

  ('63104', 'Z1S'),
  ('63111', 'Z1S'),
  ('63118', 'Z1S'),

  ('63108', 'Z2'),
  ('63110', 'Z2'),
  ('63112', 'Z2'),

  ('63109', 'Z3'),
  ('63116', 'Z3'),
  ('63139', 'Z3'),

  ('63113', 'Z4'),
  ('63115', 'Z4'),
  ('63120', 'Z4')
ON CONFLICT (zip_code) DO NOTHING;

-- Seed resource types with default capacities
INSERT INTO resource_types (resource_id, name, description, icon, display_order, capacity) VALUES
  ('R1_UAV', 'UAV Reconnaissance', 'Unmanned aerial vehicles for aerial surveillance and damage assessment', '🚁', 1, 10),
  ('R2_ENGINEERING', 'Engineering Teams', 'Specialized engineering teams for infrastructure assessment and emergency repairs', '🔧', 2, 15),
  ('R3_PUMPS', 'Water Pumps', 'High-capacity water pumps for flood water removal and drainage', '💧', 3, 20),
  ('R4_RESCUE', 'Rescue Teams', 'Swift water rescue teams and emergency response personnel', '🚤', 4, 25),
  ('R5_EVAC', 'Evacuation Support', 'Personnel and vehicles for coordinated evacuation operations', '🚐', 5, 30),
  ('R6_MEDICAL', 'Medical Strike Teams', 'Mobile medical units and emergency healthcare personnel', '⚕️', 6, 12),
  ('R7_CI', 'Critical Infrastructure', 'Teams specialized in protecting and restoring critical infrastructure', '🏭', 7, 8)
ON CONFLICT (resource_id) DO NOTHING;

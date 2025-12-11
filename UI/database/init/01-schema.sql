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

-- Seed zones
INSERT INTO zones (zone_id, name, river_proximity, elevation_risk, pop_density, crit_infra_score, hospital_count, critical_infra) VALUES
  ('Z1N', 'North Riverfront Floodplain',         0.98, 0.95, 0.75, 0.40, 1, TRUE),
  ('Z1S', 'South Riverfront Floodplain',         0.95, 0.90, 0.80, 0.50, 2, TRUE),
  ('Z2',  'Central Business & Medical Core',     0.75, 0.70, 0.90, 0.90, 6, TRUE),
  ('Z3',  'Inland South Residential Plateau',    0.40, 0.45, 0.70, 0.35, 0, FALSE),
  ('Z4',  'Inland North Residential Plateau',    0.45, 0.50, 0.75, 0.40, 0, FALSE),
  ('ZC',  'Central / Special ZIPs',              0.70, 0.70, 0.10, 0.20, 0, FALSE)
ON CONFLICT (zone_id) DO NOTHING;

-- Seed ZIP mappings
INSERT INTO zip_zones (zip_code, zone_id) VALUES
  ('63102', 'Z1N'),
  ('63101', 'Z1N'),
  ('63103', 'Z1N'),
  ('63106', 'Z1N'),
  ('63107', 'Z1N'),
  ('63147', 'Z1N'),

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
  ('63120', 'Z4'),

  ('63155', 'ZC'),
  ('63156', 'ZC'),
  ('63157', 'ZC'),
  ('63158', 'ZC'),
  ('63163', 'ZC'),
  ('63166', 'ZC'),
  ('63169', 'ZC'),
  ('63177', 'ZC'),
  ('63178', 'ZC'),
  ('63179', 'ZC'),
  ('63188', 'ZC')
ON CONFLICT (zip_code) DO NOTHING;

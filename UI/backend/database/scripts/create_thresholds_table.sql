-- Create table for storing flood threshold configuration
-- This table allows persistent storage of threshold values

CREATE TABLE IF NOT EXISTS threshold_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(50) NOT NULL UNIQUE DEFAULT 'default',
    flood_minor FLOAT NOT NULL DEFAULT 16.0,
    flood_moderate FLOAT NOT NULL DEFAULT 22.0,
    flood_major FLOAT NOT NULL DEFAULT 28.0,
    critical_probability FLOAT NOT NULL DEFAULT 0.8,
    warning_probability FLOAT NOT NULL DEFAULT 0.6,
    advisory_probability FLOAT NOT NULL DEFAULT 0.3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100) DEFAULT 'system',
    notes TEXT,

    -- Add constraints to ensure logical ordering
    CONSTRAINT chk_flood_levels CHECK (flood_minor < flood_moderate AND flood_moderate < flood_major),
    CONSTRAINT chk_probabilities CHECK (
        advisory_probability < warning_probability AND
        warning_probability < critical_probability AND
        critical_probability <= 1.0 AND
        advisory_probability >= 0.0
    )
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_threshold_config_name ON threshold_config(config_name);

-- Insert default configuration if it doesn't exist
INSERT INTO threshold_config (config_name, flood_minor, flood_moderate, flood_major, critical_probability, warning_probability, advisory_probability, notes)
VALUES (
    'default',
    16.0,   -- Minor flood level (feet)
    22.0,   -- Moderate flood level (feet)
    28.0,   -- Major flood level (feet)
    0.8,    -- Critical probability threshold
    0.6,    -- Warning probability threshold
    0.3,    -- Advisory probability threshold
    'Default flood risk thresholds for St. Louis area'
)
ON CONFLICT (config_name) DO NOTHING;

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_threshold_config_updated_at
    BEFORE UPDATE ON threshold_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
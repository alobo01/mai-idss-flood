-- Flood Prediction Database Schema
-- PostgreSQL Schema for Flood Prediction System

-- Enable PostGIS for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Geographic zones with flood risk data
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    population INTEGER DEFAULT 0,
    area_km2 DECIMAL(10,2),
    admin_level INTEGER DEFAULT 10,
    critical_assets TEXT[] DEFAULT ARRAY[]::TEXT[],
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Risk assessments over time
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    time_horizon VARCHAR(10) NOT NULL, -- '6h', '12h', '18h', '24h', '48h', '72h'
    forecast_time TIMESTAMP WITH TIME ZONE NOT NULL,
    risk_level DECIMAL(3,2) NOT NULL CHECK (risk_level >= 0 AND risk_level <= 1),
    risk_factors JSONB, -- Additional risk factors and metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Critical assets and infrastructure
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'hospital', 'school', 'power_plant', 'bridge', etc.
    criticality VARCHAR(20) DEFAULT 'medium' CHECK (criticality IN ('low', 'medium', 'high', 'critical')),
    location GEOMETRY(POINT, 4326) NOT NULL,
    address TEXT,
    capacity INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Damage assessments for assets
CREATE TABLE damage_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    assessment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    damage_level DECIMAL(3,2) NOT NULL CHECK (damage_level >= 0 AND damage_level <= 1),
    damage_type VARCHAR(100),
    estimated_cost DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'assessed' CHECK (status IN ('assessed', 'under_repair', 'repaired', 'demolished')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resources (crews, equipment, facilities)
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'crew', 'vehicle', 'equipment', 'facility', 'depot'
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'deployed', 'maintenance', 'unavailable', 'ready', 'standby', 'working', 'rest')),
    location GEOMETRY(POINT, 4326),
    capacity DECIMAL(10,2),
    capabilities JSONB,
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resource deployments
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID REFERENCES resources(id) ON DELETE CASCADE,
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    deployment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    return_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    assigned_tasks TEXT,
    actual_impact JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    alert_type VARCHAR(50) NOT NULL, -- 'flood_warning', 'resource_shortage', 'infrastructure_damage', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Communication logs
CREATE TABLE communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel VARCHAR(50) NOT NULL,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    direction VARCHAR(20) DEFAULT 'outbound' CHECK (direction IN ('inbound', 'outbound')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- River gauges and water level monitoring
CREATE TABLE gauges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    river_name VARCHAR(255),
    gauge_type VARCHAR(50) DEFAULT 'water_level',
    unit VARCHAR(20) DEFAULT 'meters',
    alert_threshold DECIMAL(10,2),
    warning_threshold DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'inactive')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gauge readings
CREATE TABLE gauge_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gauge_id UUID REFERENCES gauges(id) ON DELETE CASCADE,
    reading_value DECIMAL(10,4) NOT NULL,
    reading_time TIMESTAMP WITH TIME ZONE NOT NULL,
    quality_flag VARCHAR(20) DEFAULT 'good' CHECK (quality_flag IN ('good', 'suspect', 'bad', 'missing')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Raw hydrologic inputs
CREATE TABLE raw_data (
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model predictions
CREATE TABLE predictions (
    date DATE PRIMARY KEY,
    predicted_level DOUBLE PRECISION,
    flood_probability DOUBLE PRECISION CHECK (flood_probability >= 0 AND flood_probability <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Response plans
CREATE TABLE response_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    description TEXT,
    plan_type VARCHAR(50) NOT NULL, -- 'evacuation', 'resource_deployment', 'infrastructure_protection', etc.
    trigger_conditions JSONB,
    recommended_actions JSONB,
    required_resources JSONB,
    assignments JSONB,
    coverage JSONB,
    notes TEXT,
    estimated_duration INTEGER, -- in hours
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Administrator managed users
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    department VARCHAR(150),
    phone VARCHAR(50),
    location VARCHAR(150),
    status VARCHAR(30) DEFAULT 'active',
    zones TEXT[] DEFAULT ARRAY[]::TEXT[],
    permissions TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Administrator configured risk thresholds
CREATE TABLE admin_risk_thresholds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    band VARCHAR(50) NOT NULL,
    min_risk DECIMAL(4,2) NOT NULL CHECK (min_risk >= 0 AND min_risk <= 1),
    max_risk DECIMAL(4,2) NOT NULL CHECK (max_risk >= 0 AND max_risk <= 1),
    color VARCHAR(10),
    description TEXT,
    auto_alert BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Administrator configured gauge thresholds
CREATE TABLE admin_gauge_thresholds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gauge_code VARCHAR(50) NOT NULL,
    gauge_name VARCHAR(150) NOT NULL,
    alert_threshold DECIMAL(6,2),
    critical_threshold DECIMAL(6,2),
    unit VARCHAR(20) DEFAULT 'meters',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Administrator alert automation rules
CREATE TABLE admin_alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL,
    trigger_value VARCHAR(150) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    channels TEXT[] DEFAULT ARRAY['Dashboard']::TEXT[],
    cooldown_minutes INTEGER DEFAULT 60,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_zones_geometry ON zones USING GIST (geometry);
CREATE INDEX idx_zones_code ON zones (code);
CREATE INDEX idx_assets_location ON assets USING GIST (location);
CREATE INDEX idx_gauges_location ON gauges USING GIST (location);
CREATE UNIQUE INDEX idx_risk_assessments_zone_time ON risk_assessments (zone_id, time_horizon, forecast_time);
CREATE INDEX idx_alerts_zone_severity ON alerts (zone_id, severity);
CREATE INDEX idx_deployments_resource_time ON deployments (resource_id, deployment_time);
CREATE INDEX idx_gauge_readings_gauge_time ON gauge_readings (gauge_id, reading_time);
CREATE INDEX idx_communications_time ON communications (created_at);
CREATE INDEX idx_damage_assessments_asset_time ON damage_assessments (asset_id, assessment_time);

-- Create trigger for updating timestamp columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_zones_updated_at BEFORE UPDATE ON zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gauges_updated_at BEFORE UPDATE ON gauges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_response_plans_updated_at BEFORE UPDATE ON response_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_risk_thresholds_updated_at BEFORE UPDATE ON admin_risk_thresholds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_gauge_thresholds_updated_at BEFORE UPDATE ON admin_gauge_thresholds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_alert_rules_updated_at BEFORE UPDATE ON admin_alert_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

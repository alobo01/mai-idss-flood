# Database Schema

Complete documentation of the PostgreSQL database schema with PostGIS extensions for the Flood Prediction System.

## 🗄️ Database Overview

### Configuration
- **Database**: PostgreSQL 15
- **Extensions**: PostGIS 3.3
- **Character Set**: UTF-8
- **Collation**: C (case-sensitive)
- **Timezone**: UTC

### Key Features
- **Geospatial Support**: Full PostGIS integration for flood zone mapping
- **UUID Primary Keys**: All tables use UUID for primary identification
- **Timestamp Tracking**: Created/updated timestamps for data auditing
- **Foreign Key Constraints**: Referential integrity across related tables
- **Spatial Indexing**: Optimized for geospatial queries

## 📋 Table Schema

### 1. zones - Geographic Flood Zones

Stores flood-prone geographic areas with demographic and critical asset information.

```sql
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    population INTEGER DEFAULT 0,
    area_km2 DECIMAL(10,2),
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_zones_geometry ON zones USING GIST (geometry);
CREATE INDEX idx_zones_name ON zones (name);
```

**Fields:**
- `id` - Unique identifier for the zone
- `name` - Human-readable zone name
- `description` - Zone description and characteristics
- `population` - Total population in the zone
- `area_km2` - Geographic area in square kilometers
- `geometry` - PostGIS polygon representing zone boundaries (SRID 4326)
- `created_at`, `updated_at` - Audit timestamps

**Sample Data:**
```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "name": "Riverside North",
  "description": "Northern riverside residential area",
  "population": 12450,
  "area_km2": 15.2,
  "geometry": "POLYGON((-3.71 40.41, -3.70 40.41, -3.70 40.42, -3.71 40.42, -3.71 40.41))"
}
```

### 2. risk_assessments - Flood Risk Predictions

Time-based flood risk assessments for different forecast horizons.

```sql
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    time_horizon VARCHAR(10) NOT NULL CHECK (time_horizon IN ('6h', '12h', '18h', '24h', '48h', '72h')),
    forecast_time TIMESTAMP WITH TIME ZONE NOT NULL,
    risk_level DECIMAL(3,2) NOT NULL CHECK (risk_level >= 0 AND risk_level <= 1),
    risk_factors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_risk_zone_time ON risk_assessments (zone_id, forecast_time);
CREATE INDEX idx_risk_forecast_time ON risk_assessments (forecast_time);
CREATE INDEX idx_risk_time_horizon ON risk_assessments (time_horizon);
```

**Fields:**
- `zone_id` - Foreign key to zones table
- `time_horizon` - Forecast time horizon (6h to 72h)
- `forecast_time` - Target time for the prediction
- `risk_level` - Risk level (0.0 to 1.0, where 1.0 is highest risk)
- `risk_factors` - JSON object with contributing factors

**Risk Factors Example:**
```json
{
  "precipitation": 45.2,
  "riverLevel": 3.8,
  "soilSaturation": 87,
  "temperature": 15.5,
  "windSpeed": 12.3,
  "atmosphericPressure": 1013.2
}
```

### 3. assets - Critical Infrastructure

Critical infrastructure assets within flood zones.

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('hospital', 'school', 'power_plant', 'bridge', 'road', 'water_treatment', 'government', 'commercial', 'emergency_services')),
    criticality VARCHAR(20) DEFAULT 'medium' CHECK (criticality IN ('low', 'medium', 'high', 'critical')),
    location GEOMETRY(POINT, 4326) NOT NULL,
    address TEXT,
    capacity INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_assets_location ON assets USING GIST (location);
CREATE INDEX idx_assets_zone_id ON assets (zone_id);
CREATE INDEX idx_assets_type ON assets (type);
CREATE INDEX idx_assets_criticality ON assets (criticality);
```

**Asset Types:**
- `hospital` - Medical facilities
- `school` - Educational institutions
- `power_plant` - Energy infrastructure
- `bridge` - Transportation infrastructure
- `road` - Major roadways
- `water_treatment` - Water facilities
- `government` - Government buildings
- `commercial` - Business infrastructure
- `emergency_services` - Police, fire stations

### 4. damage_assessments - Infrastructure Damage Reports

Damage evaluation and assessment records for assets.

```sql
CREATE TABLE damage_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    assessment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    damage_level DECIMAL(3,2) NOT NULL CHECK (damage_level >= 0 AND damage_level <= 1),
    damage_type VARCHAR(50) CHECK (damage_type IN ('structural', 'water_damage', 'debris', 'electrical', 'access', 'fire')),
    estimated_cost DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'reported' CHECK (status IN ('reported', 'assessed', 'repaired')),
    notes TEXT,
    assessed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_damage_asset_time ON damage_assessments (asset_id, assessment_time);
CREATE INDEX idx_damage_status ON damage_assessments (status);
CREATE INDEX idx_damage_assessment_time ON damage_assessments (assessment_time);
```

**Damage Levels:**
- `0.0` - No damage
- `0.1-0.3` - Minor damage
- `0.4-0.6` - Moderate damage
- `0.7-1.0` - Severe damage

### 5. resources - Emergency Resources

Emergency teams, equipment, and supplies.

```sql
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('emergency_crew', 'fire_crew', 'medical_crew', 'engineering_crew', 'equipment', 'supplies', 'vehicle')),
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'deployed', 'standby', 'maintenance', 'decommissioned')),
    location GEOMETRY(POINT, 4326),
    capacity INTEGER,
    capabilities JSONB,
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_resources_location ON resources USING GIST (location);
CREATE INDEX idx_resources_type ON resources (type);
CREATE INDEX idx_resources_status ON resources (status);
```

**Resource Types:**
- `emergency_crew` - Search and rescue teams
- `fire_crew` - Firefighting personnel
- `medical_crew` - Medical response teams
- `engineering_crew` - Infrastructure repair teams
- `equipment` - Heavy machinery and tools
- `supplies` - Emergency provisions
- `vehicle` - Transportation assets

**Capabilities Example:**
```json
["medical", "rescue", "evacuation", "water_rescue", "structural_rescue"]
```

### 6. deployments - Resource Deployment Tracking

Records of resource deployments to specific zones.

```sql
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID REFERENCES resources(id) ON DELETE CASCADE,
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    deployment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    return_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    purpose TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_deployments_resource ON deployments (resource_id);
CREATE INDEX idx_deployments_zone ON deployments (zone_id);
CREATE INDEX idx_deployments_status ON deployments (status);
CREATE INDEX idx_deployments_time ON deployments (deployment_time);
```

### 7. alerts - System Notifications

System alerts and emergency notifications.

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alerts_zone ON alerts (zone_id);
CREATE INDEX idx_alerts_severity ON alerts (severity);
CREATE idx_alerts_status ON alerts (acknowledged, resolved);
CREATE INDEX idx_alerts_created ON alerts (created_at);
```

**Alert Types:**
- `flood_warning` - River level warnings
- `evacuation` - Evacuation orders
- `infrastructure` - Infrastructure failures
- `weather` - Severe weather alerts
- `communication` - System communication
- `information` - General information

### 8. communications - Communication Records

Logs of all emergency communications sent and received.

```sql
CREATE TABLE communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('sms', 'email', 'radio', 'phone', 'social', 'public')),
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    direction VARCHAR(20) DEFAULT 'outbound' CHECK (direction IN ('inbound', 'outbound')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_communications_channel ON communications (channel);
CREATE INDEX idx_communications_priority ON communications (priority);
CREATE INDEX idx_communications_status ON communications (status);
CREATE INDEX idx_communications_created ON communications (created_at);
```

### 9. gauges - River Monitoring Stations

River gauge stations for water level monitoring.

```sql
CREATE TABLE gauges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    river_name VARCHAR(255),
    gauge_type VARCHAR(50) NOT NULL CHECK (gauge_type IN ('water_level', 'flow_rate', 'precipitation')),
    unit VARCHAR(20) NOT NULL,
    alert_threshold DECIMAL(10,2),
    warning_threshold DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_gauges_location ON gauges USING GIST (location);
CREATE INDEX idx_gauges_river ON gauges (river_name);
CREATE INDEX idx_gauges_status ON gauges (status);
```

### 10. gauge_readings - Historical Gauge Data

Time-series data from river gauge stations.

```sql
CREATE TABLE gauge_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gauge_id UUID REFERENCES gauges(id) ON DELETE CASCADE,
    reading_value DECIMAL(10,4) NOT NULL,
    reading_time TIMESTAMP WITH TIME ZONE NOT NULL,
    quality_flag VARCHAR(20) DEFAULT 'good' CHECK (quality_flag IN ('good', 'suspect', 'bad', 'missing')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_gauge_readings_gauge_time ON gauge_readings (gauge_id, reading_time);
CREATE INDEX idx_gauge_readings_time ON gauge_readings (reading_time);
```

**Quality Flags:**
- `good` - High quality reading
- `suspect` - Questionable quality
- `bad` - Low quality or error
- `missing` - No data available

### 11. response_plans - Emergency Procedures

Pre-defined emergency response plans and procedures.

```sql
CREATE TABLE response_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    plan_type VARCHAR(50) NOT NULL CHECK (plan_type IN ('evacuation', 'shelter', 'medical', 'infrastructure', 'communication')),
    trigger_conditions TEXT[],
    recommended_actions TEXT[],
    required_resources TEXT[],
    estimated_duration VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_response_plans_type ON response_plans (plan_type);
CREATE INDEX idx_response_plans_status ON response_plans (status);
CREATE INDEX idx_response_plans_priority ON response_plans (priority);
```

## 🔄 Relationships

### Entity Relationship Diagram

```
zones (1) ────────┐
│                  │
│                  │
│                  ▼
│             risk_assessments (*)
│                  │
│                  ▼
│             assets (*)
│                  │
│                  ▼
│        damage_assessments (*)
│
│                  │
│                  ▼
│              alerts (*)
│
│                  │
│                  ▼
│         communications (*)
│
│                  │
│                  ▼
│              gauges (*)
│                  │
│                  ▼
│         gauge_readings (*)
│
resources (*) ─── deployments (*) ──── zones (*)
```

### Foreign Key Relationships

1. **zones** → risk_assessments (1:N) - Risk assessments for zones
2. **zones** → assets (1:N) - Assets located in zones
3. **zones** → alerts (1:N) - Alerts for zones
4. **assets** → damage_assessments (1:N) - Damage reports for assets
5. **resources** → deployments (1:N) - Resource deployment records
6. **deployments** → zones (N:1) - Deployments to zones
7. **gauges** → gauge_readings (1:N) - Time series readings

## 🗺️ Spatial Features

### PostGIS Extensions
- `postgis` - Core spatial functionality
- `uuid-ossp` - UUID generation functions
- PostGIS version 3.3.3 for advanced spatial analysis

### Spatial Indexing
- **GIST Indexes** on geometry columns for fast spatial queries
- **B-Tree Indexes** on non-spatial columns for standard queries
- **Combined Indexes** for common spatial + attribute queries

### Common Spatial Queries

```sql
-- Find zones containing a point
SELECT * FROM zones
WHERE ST_Contains(geometry, ST_MakePoint(-3.705, 40.415, 4326));

-- Find assets within distance of a zone
SELECT a.* FROM assets a, zones z
WHERE ST_DWithin(a.location, z.geometry, 1000)
AND z.id = 'zone-uuid';

-- Calculate zone area
SELECT name, ST_Area(geometry) / 1000000 as area_sq_km
FROM zones;
```

## 📊 Data Types and Constraints

### Numeric Types
- `DECIMAL(10,2)` - Monetary values, precise measurements
- `DECIMAL(3,2)` - Percentages and ratios
- `DECIMAL(10,4)` - High-precision measurements
- `INTEGER` - Counts and quantities

### String Types
- `VARCHAR(255)` - Names, titles, identifiers
- `TEXT` - Descriptions, notes, content
- `UUID` - Primary keys and foreign keys

### Temporal Types
- `TIMESTAMP WITH TIME ZONE` - All timestamps in UTC
- `DATE` - Date-only values (if needed)
- `TIME` - Time-only values (if needed)

### Boolean Types
- `BOOLEAN` - Flags and status indicators

### JSONB Types
- `JSONB` - Structured metadata and flexible attributes
- Supports indexing and JSON queries

## 🔧 Indexing Strategy

### Performance Indexes
1. **Primary Key Indexes** - Automatic on UUID primary keys
2. **Foreign Key Indexes** - Fast join performance
3. **GIST Spatial Indexes** - Geospatial query optimization
4. **Time-Based Indexes** - Chronological queries
5. **Status/Type Indexes** - Filtering and lookup queries

### Composite Indexes
```sql
-- Zone and time for risk assessments
CREATE INDEX idx_risk_zone_time ON risk_assessments (zone_id, forecast_time DESC);

-- Asset and criticality for prioritization
CREATE INDEX idx_assets_criticality ON assets (type, criticality DESC);
```

## 🚀 Migration Strategy

### Schema Versioning
- Use migration files with version numbers
- Track applied migrations in a migrations table
- Support rollback for development environments

### Data Population
- Initial data loading from GeoJSON files
- Referential integrity checks
- Sample data for development and testing

---

**Last Updated**: 2025-11-13
**Database Version**: PostgreSQL 15 + PostGIS 3.3
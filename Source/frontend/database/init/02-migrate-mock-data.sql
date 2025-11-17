-- Import mock data into PostgreSQL database
-- This script migrates the JSON-based mock data to the relational database

-- Insert sample zones (based on zones.geojson)
INSERT INTO zones (id, code, name, description, population, area_km2, admin_level, critical_assets, geometry) VALUES
(
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    'Z-ALFA',
    'Downtown River District',
    'Central business district along the main river channel',
    15000,
    12.5,
    10,
    ARRAY['Hospital HN1', 'Downtown Elementary School'],
    ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0060,40.7128],[-74.0050,40.7138],[-74.0040,40.7128],[-74.0050,40.7118],[-74.0060,40.7128]]]}', 4326)
),
(
    '550e8400-e29b-41d4-a716-446655440002'::UUID,
    'Z-BRAVO',
    'Riverside Residential',
    'Residential area on the eastern flood plain',
    8500,
    8.3,
    10,
    ARRAY['East Side Power Station'],
    ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0050,40.7148],[-74.0040,40.7158],[-74.0030,40.7148],[-74.0040,40.7138],[-74.0050,40.7148]]]}', 4326)
),
(
    '550e8400-e29b-41d4-a716-446655440003'::UUID,
    'Z-CHARLIE',
    'Industrial Zone North',
    'Manufacturing and warehouse district',
    3500,
    15.7,
    10,
    ARRAY['Main Street Bridge'],
    ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0070,40.7138],[-74.0060,40.7148],[-74.0050,40.7138],[-74.0060,40.7128],[-74.0070,40.7138]]]}', 4326)
),
(
    '550e8400-e29b-41d4-a716-446655440004'::UUID,
    'Z-DELTA',
    'Lowland Parks',
    'Recreational areas and green spaces',
    1200,
    22.1,
    10,
    ARRAY['Riverside Water Treatment'],
    ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0040,40.7118],[-74.0030,40.7128],[-74.0020,40.7118],[-74.0030,40.7108],[-74.0040,40.7118]]]}', 4326)
);

-- Insert critical assets
INSERT INTO assets (id, zone_id, name, type, criticality, location, address, capacity, metadata) VALUES
(
    '660e8400-e29b-41d4-a716-446655440001'::UUID,
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    'City General Hospital',
    'hospital',
    'critical',
    ST_SetSRID(ST_MakePoint(-74.0055, 40.7133), 4326),
    '123 Main St, Downtown',
    350,
    '{"emergency_services": true, "icu_beds": 50, "helipad": true}'
),
(
    '660e8400-e29b-41d4-a716-446655440002'::UUID,
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    'Downtown Elementary School',
    'school',
    'high',
    ST_SetSRID(ST_MakePoint(-74.0045, 40.7123), 4326),
    '45 Oak Ave, Downtown',
    450,
    '{"grades": "K-5", "shelter_capacity": 200}'
),
(
    '660e8400-e29b-41d4-a716-446655440003'::UUID,
    '550e8400-e29b-41d4-a716-446655440002'::UUID,
    'East Side Power Station',
    'power_plant',
    'critical',
    ST_SetSRID(ST_MakePoint(-74.0035, 40.7143), 4326),
    '789 Power Rd, Riverside',
    100,
    '{"capacity_mw": 250, "fuel_type": "natural_gas", "backup_generators": true}'
),
(
    '660e8400-e29b-41d4-a716-446655440004'::UUID,
    '550e8400-e29b-41d4-a716-446655440003'::UUID,
    'Main Street Bridge',
    'bridge',
    'high',
    ST_SetSRID(ST_MakePoint(-74.0065, 40.7143), 4326),
    'Main St crossing Industrial Zone',
    50000,
    '{"year_built": 1985, "bridge_type": "steel_truss", "clearance_height": "15ft"}'
),
(
    '660e8400-e29b-41d4-a716-446655440005'::UUID,
    '550e8400-e29b-41d4-a716-446655440004'::UUID,
    'Riverside Water Treatment',
    'water_facility',
    'critical',
    ST_SetSRID(ST_MakePoint(-74.0035, 40.7113), 4326),
    '321 River Rd, Lowland Parks',
    100,
    '{"daily_capacity_gallons": 5000000, "backup_power": true}'
);

-- Insert current risk assessments for multiple time horizons
INSERT INTO risk_assessments (zone_id, time_horizon, forecast_time, risk_level, risk_factors) VALUES
-- 6-hour forecast
('550e8400-e29b-41d4-a716-446655440001'::UUID, '6h', NOW() + INTERVAL '6 hours', 0.65, '{"precipitation": 2.3, "river_level": 3.1, "soil_saturation": 0.78}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '6h', NOW() + INTERVAL '6 hours', 0.58, '{"precipitation": 2.1, "river_level": 2.8, "soil_saturation": 0.72}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '6h', NOW() + INTERVAL '6 hours', 0.42, '{"precipitation": 1.8, "river_level": 2.2, "soil_saturation": 0.65}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '6h', NOW() + INTERVAL '6 hours', 0.71, '{"precipitation": 2.5, "river_level": 3.4, "soil_saturation": 0.82}'),

-- 12-hour forecast
('550e8400-e29b-41d4-a716-446655440001'::UUID, '12h', NOW() + INTERVAL '12 hours', 0.72, '{"precipitation": 3.1, "river_level": 3.8, "soil_saturation": 0.85}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '12h', NOW() + INTERVAL '12 hours', 0.68, '{"precipitation": 2.9, "river_level": 3.5, "soil_saturation": 0.80}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '12h', NOW() + INTERVAL '12 hours', 0.55, '{"precipitation": 2.4, "river_level": 2.9, "soil_saturation": 0.72}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '12h', NOW() + INTERVAL '12 hours', 0.78, '{"precipitation": 3.3, "river_level": 4.1, "soil_saturation": 0.88}'),

-- 24-hour forecast
('550e8400-e29b-41d4-a716-446655440001'::UUID, '24h', NOW() + INTERVAL '24 hours', 0.81, '{"precipitation": 4.2, "river_level": 4.8, "soil_saturation": 0.92}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '24h', NOW() + INTERVAL '24 hours', 0.76, '{"precipitation": 3.8, "river_level": 4.3, "soil_saturation": 0.88}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '24h', NOW() + INTERVAL '24 hours', 0.63, '{"precipitation": 3.1, "river_level": 3.6, "soil_saturation": 0.78}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '24h', NOW() + INTERVAL '24 hours', 0.85, '{"precipitation": 4.5, "river_level": 5.2, "soil_saturation": 0.95}'),

-- 48-hour forecast
('550e8400-e29b-41d4-a716-446655440001'::UUID, '48h', NOW() + INTERVAL '48 hours', 0.74, '{"precipitation": 3.5, "river_level": 4.1, "soil_saturation": 0.86}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '48h', NOW() + INTERVAL '48 hours', 0.69, '{"precipitation": 3.2, "river_level": 3.7, "soil_saturation": 0.82}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '48h', NOW() + INTERVAL '48 hours', 0.58, '{"precipitation": 2.7, "river_level": 3.0, "soil_saturation": 0.73}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '48h', NOW() + INTERVAL '48 hours', 0.79, '{"precipitation": 3.8, "river_level": 4.6, "soil_saturation": 0.90}');

-- Insert damage assessments
INSERT INTO damage_assessments (asset_id, assessment_time, damage_level, damage_type, estimated_cost, status, notes) VALUES
('660e8400-e29b-41d4-a716-446655440001'::UUID, NOW() - INTERVAL '2 hours', 0.15, 'water_damage', 45000, 'assessed', 'Minor flooding in basement, equipment needs drying'),
('660e8400-e29b-41d4-a716-446655440003'::UUID, NOW() - INTERVAL '4 hours', 0.25, 'electrical_damage', 120000, 'under_repair', 'Transformer damaged due to water exposure'),
('660e8400-e29b-41d4-a716-446655440004'::UUID, NOW() - INTERVAL '1 hour', 0.10, 'structural', 25000, 'assessed', 'Minor erosion around bridge supports');

-- Insert resources
INSERT INTO resources (id, code, name, type, status, location, capacity, capabilities, contact_info) VALUES
(
    '770e8400-e29b-41d4-a716-446655440010'::UUID,
    'D-CENTRAL',
    'Central Depot',
    'depot',
    'available',
    ST_SetSRID(ST_MakePoint(-3.7033, 40.4167), 4326),
    1000,
    '{"lat": 40.4167, "lng": -3.7033, "storage_units": 5}',
    '{"address": "123 Logistics Ave"}'
),
(
    '770e8400-e29b-41d4-a716-446655440011'::UUID,
    'D-EAST',
    'East Yard',
    'depot',
    'available',
    ST_SetSRID(ST_MakePoint(-3.6800, 40.4190), 4326),
    800,
    '{"lat": 40.4190, "lng": -3.6800, "storage_units": 4}',
    '{"address": "45 Riverbank Rd"}'
),
(
    '770e8400-e29b-41d4-a716-446655440012'::UUID,
    'D-SOUTH',
    'South Facility',
    'depot',
    'available',
    ST_SetSRID(ST_MakePoint(-3.7150, 40.4080), 4326),
    650,
    '{"lat": 40.4080, "lng": -3.7150, "storage_units": 3}',
    '{"address": "300 Delta Ave"}'
),
(
    '770e8400-e29b-41d4-a716-446655440020'::UUID,
    'P-001',
    'Pump P-001',
    'equipment',
    'available',
    ST_SetSRID(ST_MakePoint(-3.7033, 40.4167), 4326),
    300,
    '{"depot": "D-CENTRAL", "type": "Pump", "capacity_lps": 300}',
    '{}'
),
(
    '770e8400-e29b-41d4-a716-446655440021'::UUID,
    'P-002',
    'Pump P-002',
    'equipment',
    'available',
    ST_SetSRID(ST_MakePoint(-3.6800, 40.4190), 4326),
    250,
    '{"depot": "D-EAST", "type": "Pump", "capacity_lps": 250}',
    '{}'
),
(
    '770e8400-e29b-41d4-a716-446655440022'::UUID,
    'P-003',
    'Pump P-003',
    'equipment',
    'available',
    ST_SetSRID(ST_MakePoint(-3.7150, 40.4080), 4326),
    400,
    '{"depot": "D-SOUTH", "type": "Pump", "capacity_lps": 400}',
    '{}'
),
(
    '770e8400-e29b-41d4-a716-446655440023'::UUID,
    'S-010',
    'Sandbag Set S-010',
    'equipment',
    'available',
    ST_SetSRID(ST_MakePoint(-3.6800, 40.4190), 4326),
    800,
    '{"depot": "D-EAST", "type": "Sandbags", "units": 800}',
    '{}'
),
(
    '770e8400-e29b-41d4-a716-446655440024'::UUID,
    'S-011',
    'Sandbag Set S-011',
    'equipment',
    'available',
    ST_SetSRID(ST_MakePoint(-3.7033, 40.4167), 4326),
    1200,
    '{"depot": "D-CENTRAL", "type": "Sandbags", "units": 1200}',
    '{}'
),
(
    '770e8400-e29b-41d4-a716-446655440025'::UUID,
    'S-012',
    'Sandbag Set S-012',
    'equipment',
    'available',
    ST_SetSRID(ST_MakePoint(-3.7150, 40.4080), 4326),
    600,
    '{"depot": "D-SOUTH", "type": "Sandbags", "units": 600}',
    '{}'
),
(
    '770e8400-e29b-41d4-a716-446655440030'::UUID,
    'C-A1',
    'Alpha Crew',
    'crew',
    'ready',
    ST_SetSRID(ST_MakePoint(-3.7050, 40.4172), 4326),
    12,
    '{"skills": ["pumping", "evacuation"], "depot": "D-CENTRAL"}',
    '{"phone": "555-0101", "radio": "Channel 1"}'
),
(
    '770e8400-e29b-41d4-a716-446655440031'::UUID,
    'C-B3',
    'Bravo Crew',
    'crew',
    'ready',
    ST_SetSRID(ST_MakePoint(-3.6820, 40.4201), 4326),
    10,
    '{"skills": ["roadblock", "rescue"], "depot": "D-EAST"}',
    '{"phone": "555-0102", "radio": "Channel 2"}'
),
(
    '770e8400-e29b-41d4-a716-446655440032'::UUID,
    'C-C2',
    'Charlie Crew',
    'crew',
    'ready',
    ST_SetSRID(ST_MakePoint(-3.7128, 40.4095), 4326),
    8,
    '{"skills": ["pumping", "medical"], "depot": "D-SOUTH"}',
    '{"phone": "555-0103", "radio": "Channel 3"}'
),
(
    '770e8400-e29b-41d4-a716-446655440033'::UUID,
    'C-D4',
    'Delta Crew',
    'crew',
    'ready',
    ST_SetSRID(ST_MakePoint(-3.7021, 40.4168), 4326),
    8,
    '{"skills": ["evacuation", "logistics"], "depot": "D-CENTRAL"}',
    '{"phone": "555-0104", "radio": "Channel 4"}'
);

-- Insert current deployments
INSERT INTO deployments (resource_id, zone_id, deployment_time, status, assigned_tasks, actual_impact) VALUES
('770e8400-e29b-41d4-a716-446655440002'::UUID, '550e8400-e29b-41d4-a716-446655440001'::UUID, NOW() - INTERVAL '3 hours', 'active', 'Pump water from basement areas, clear debris', '{"water_removed_gallons": 15000, "debris_cleared_tons": 5}'),
('770e8400-e29b-41d4-a716-446655440001'::UUID, '550e8400-e29b-41d4-a716-446655440004'::UUID, NOW() - INTERVAL '6 hours', 'active', 'Rescue operations, evacuation assistance', '{"people_evacuated": 25, "rescues": 3}');

-- Insert sample alerts
INSERT INTO alerts (zone_id, severity, alert_type, title, message, acknowledged, metadata) VALUES
('550e8400-e29b-41d4-a716-446655440001'::UUID, 'high', 'flood_warning', 'Flash Flood Warning Downtown', 'Heavy rainfall expected to cause flash flooding in Downtown River District within 6 hours. Prepare for evacuation.', false, '{"expected_depth": "2-3 feet", "affected_areas": ["basements", "low-lying streets"]}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, 'medium', 'infrastructure_damage', 'Power Station Alert', 'Water levels approaching critical thresholds at East Side Power Station. Backup systems engaged.', true, '{"system_status": "backup_power_active", "crew_dispatched": true}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, 'high', 'resource_shortage', 'Equipment Shortage', 'Additional pumps needed for Lowland Parks area. Current capacity insufficient.', false, '{"pumps_needed": 5, "pumps_available": 2, "urgency": "high"}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, 'critical', 'evacuation_order', 'Mandatory Evacuation Order', 'Mandatory evacuation ordered for Riverside Residential due to rising floodwaters. Assembly point: North Community Center.', false, '{"evacuation_deadline": "2 hours", "transportation_available": true, "shelter_capacity": 150}');

-- Insert sample communications
INSERT INTO communications (channel, sender, recipient, message, direction, priority, status, metadata) VALUES
('radio', 'Command Center', 'Team Alpha', 'Report status of evacuation operations in Downtown District', 'outbound', 'high', 'delivered', '{"timestamp": "2025-11-12T10:30:00Z", "ack_required": true}'),
('email', 'weather.service@noaa.gov', 'flood-control@city.gov', 'Updated rainfall forecast: Additional 2-3 inches expected in next 6 hours', 'inbound', 'high', 'delivered', '{"attachment": "forecast_map.pdf"}'),
('sms', 'Alert System', 'All Residents', 'EVACUATION ORDER: Riverside Residential must evacuate immediately. Proceed to North Community Center.', 'outbound', 'urgent', 'delivered', '{"recipients": 850, "delivery_rate": "98%"}'),
('phone', 'Resident - 123 Oak St', 'Emergency Hotline', 'My basement is flooding and I need help evacuating my elderly mother', 'inbound', 'high', 'delivered', '{"caller_location_confirmed": true, "dispatch_team": "Team Alpha"}'),
('radio', 'Team Alpha', 'Command Center', 'Evacuation operations in Riverside progressing. 25 residents evacuated, 3 rescues completed. Requesting additional transport.', 'inbound', 'high', 'delivered', '{"team_status": "operational", "fuel_remaining": "60%"}');

-- Insert river gauges
INSERT INTO gauges (id, code, name, location, river_name, gauge_type, unit, alert_threshold, warning_threshold, status, metadata) VALUES
(
    '880e8400-e29b-41d4-a716-446655440001'::UUID,
    'G-RIV-12',
    'Main Street Bridge Gauge',
    ST_SetSRID(ST_MakePoint(-74.0060, 40.7140), 4326),
    'City River',
    'water_level',
    'meters',
    4.5,
    3.5,
    'active',
    '{"datum": "NAVD88", "zero_gauge_elevation": 10.5, "flood_stage": 4.0}'
),
(
    '880e8400-e29b-41d4-a716-446655440002'::UUID,
    'G-RIV-08',
    'Industrial Park Gauge',
    ST_SetSRID(ST_MakePoint(-74.0050, 40.7130), 4326),
    'City River',
    'water_level',
    'meters',
    4.2,
    3.2,
    'active',
    '{"datum": "NAVD88", "zero_gauge_elevation": 9.8, "flood_stage": 3.7}'
),
(
    '880e8400-e29b-41d4-a716-446655440003'::UUID,
    'G-RIV-15',
    'Lowland Parks Gauge',
    ST_SetSRID(ST_MakePoint(-74.0030, 40.7110), 4326),
    'East Branch River',
    'water_level',
    'meters',
    3.8,
    2.8,
    'active',
    '{"datum": "NAVD88", "zero_gauge_elevation": 8.2, "flood_stage": 3.3}'
);

-- Insert recent gauge readings (last 24 hours)
INSERT INTO gauge_readings (gauge_id, reading_value, reading_time, quality_flag) VALUES
-- Main Street Bridge readings
('880e8400-e29b-41d4-a716-446655440001'::UUID, 2.8, NOW() - INTERVAL '24 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440001'::UUID, 3.1, NOW() - INTERVAL '18 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440001'::UUID, 3.5, NOW() - INTERVAL '12 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440001'::UUID, 3.8, NOW() - INTERVAL '6 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440001'::UUID, 4.1, NOW() - INTERVAL '1 hour', 'good'),

-- Industrial Park readings
('880e8400-e29b-41d4-a716-446655440002'::UUID, 2.6, NOW() - INTERVAL '24 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440002'::UUID, 2.9, NOW() - INTERVAL '18 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440002'::UUID, 3.2, NOW() - INTERVAL '12 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440002'::UUID, 3.6, NOW() - INTERVAL '6 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440002'::UUID, 3.9, NOW() - INTERVAL '1 hour', 'good'),

-- Lowland Parks readings
('880e8400-e29b-41d4-a716-446655440003'::UUID, 2.1, NOW() - INTERVAL '24 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440003'::UUID, 2.4, NOW() - INTERVAL '18 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440003'::UUID, 2.8, NOW() - INTERVAL '12 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440003'::UUID, 3.2, NOW() - INTERVAL '6 hours', 'good'),
('880e8400-e29b-41d4-a716-446655440003'::UUID, 3.5, NOW() - INTERVAL '1 hour', 'good');

-- Insert response plans
INSERT INTO response_plans (name, version, description, plan_type, trigger_conditions, recommended_actions, required_resources, assignments, coverage, notes, estimated_duration, priority, status) VALUES
(
    'Urban Flood Response Plan',
    '2025-11-11T10:30:00Z',
    'Operational response derived from 12h horizon with severe risk band.',
    'resource_deployment',
    '{"water_level_threshold": 3.5, "rainfall_rate": "1in/hr", "forecast_confidence": 0.8}',
    '["Issue evacuation orders", "Open emergency shelters", "Deploy transport resources", "Coordinate with law enforcement"]',
    '{"pumps": 3, "sandbags": 1200, "crews": 4}',
    '[
      {"zoneId": "Z-ALFA", "priority": 1, "actions": [
        {"type": "deploy_pump", "qty": 1, "from": "D-CENTRAL", "equipment": "P-001"},
        {"type": "lay_sandbags", "qty": 200, "from": "D-EAST", "equipment": "S-010"},
        {"type": "assign_crew", "crew": "C-A1", "task": "pumping_operation"}
      ]},
      {"zoneId": "Z-ECHO", "priority": 2, "actions": [
        {"type": "deploy_pump", "qty": 1, "from": "D-SOUTH", "equipment": "P-003"},
        {"type": "lay_sandbags", "qty": 300, "from": "D-CENTRAL", "equipment": "S-011"},
        {"type": "assign_crew", "crew": "C-C2", "task": "flood_response"},
        {"type": "evacuation", "crew": "C-D4", "target": "Stadium ST1"}
      ]},
      {"zoneId": "Z-CHARLIE", "priority": 3, "actions": [
        {"type": "lay_sandbags", "qty": 150, "from": "D-SOUTH", "equipment": "S-012"},
        {"type": "assign_crew", "crew": "C-B3", "task": "access_protection"}
      ]}
    ]',
    '{"total_zones": 5, "covered_zones": 3, "coverage_percentage": 60, "resources_deployed": {"pumps": 2, "sandbags": 650, "crews": 3}}',
    'Focus on high-risk residential zones while preparing evacuation corridors.',
    8,
    'high',
    'active'
),
(
    'Infrastructure Protection Protocol',
    '2025-11-10T08:00:00Z',
    'Protect critical infrastructure from flood damage',
    'infrastructure_protection',
    '{"water_level_threshold": 2.8, "lead_time_hours": 6}',
    '["Deploy flood barriers", "Pump out critical facilities", "Shut down non-essential systems", "Backup critical data", "Staff emergency generators"]',
    '{"crews": 3, "vehicles": 8, "equipment": ["pumps", "sandbags", "generators", "fuel"]}',
    '[]',
    '{"total_zones": 4, "covered_zones": 2, "coverage_percentage": 50}',
    'Prioritize power and water assets.',
    12,
    'critical',
    'active'
),
(
    'Rapid Resource Deployment',
    '2025-11-09T16:30:00Z',
    'Quick deployment of emergency resources to affected areas',
    'resource_deployment',
    '{"alert_severity": "high", "affected_population": 100}',
    '["Assess resource needs", "Deploy nearest available resources", "Establish command post", "Coordinate with other agencies"]',
    '{"crews": 2, "vehicles": 6, "equipment": ["command_vehicle", "communications", "medical_supplies"]}',
    '[]',
    '{"total_zones": 3, "covered_zones": 1, "coverage_percentage": 33}',
    'Use for rapid response drills.',
    4,
    'medium',
    'active'
);

COMMIT;

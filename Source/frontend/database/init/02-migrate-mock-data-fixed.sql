-- Import mock data into PostgreSQL database
-- This script migrates the JSON-based mock data to the relational database

-- Insert zones with proper UUID casting and PostGIS functions
INSERT INTO zones (id, code, name, description, population, area_km2, geometry) VALUES
('550e8400-e29b-41d4-a716-446655440001'::UUID,
 'Z-DOWNTOWN',
 'Downtown River District',
 'Central business district along the main river channel',
 15000,
 12.5,
 ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0060,40.7128],[-74.0050,40.7138],[-74.0040,40.7128],[-74.0050,40.7118],[-74.0060,40.7128]]]}'), 4326)
),
('550e8400-e29b-41d4-a716-446655440002'::UUID,
 'Z-RIVERSIDE',
 'Riverside Residential',
 'Residential area on the eastern flood plain',
 8500,
 8.3,
 ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0050,40.7148],[-74.0040,40.7158],[-74.0030,40.7148],[-74.0040,40.7138],[-74.0050,40.7148]]]}'), 4326)
),
('550e8400-e29b-41d4-a716-446655440003'::UUID,
 'Z-INDUSTRIAL',
 'Industrial Zone North',
 'Manufacturing and warehouse district',
 3500,
 15.7,
 ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0070,40.7138],[-74.0060,40.7148],[-74.0050,40.7138],[-74.0060,40.7128],[-74.0070,40.7138]]]}'), 4326)
),
('550e8400-e29b-41d4-a716-446655440004'::UUID,
 'Z-LOWLAND',
 'Lowland Parks',
 'Recreational areas and green spaces',
 1200,
 22.1,
 ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[-74.0040,40.7118],[-74.0030,40.7128],[-74.0020,40.7118],[-74.0030,40.7108],[-74.0040,40.7118]]]}'), 4326)
);

-- Insert assets with proper UUIDs
INSERT INTO assets (id, zone_id, name, type, criticality, location, address, capacity, metadata) VALUES
('660e8400-e29b-41d4-a716-446655440001'::UUID,
 '550e8400-e29b-41d4-a716-446655440001'::UUID,
 'City General Hospital',
 'hospital',
 'critical',
 ST_SetSRID(ST_MakePoint(-74.0055, 40.7133), 4326),
 '123 Main St, Downtown',
 350,
 '{"emergency_services": true, "icu_beds": 50, "helipad": true}'
),
('660e8400-e29b-41d4-a716-446655440002'::UUID,
 '550e8400-e29b-41d4-a716-446655440001'::UUID,
 'Downtown Elementary School',
 'school',
 'high',
 ST_SetSRID(ST_MakePoint(-74.0045, 40.7123), 4326),
 '45 Oak Ave, Downtown',
 450,
 '{"grades": "K-5", "shelter_capacity": 200}'
),
('660e8400-e29b-41d4-a716-446655440003'::UUID,
 '550e8400-e29b-41d4-a716-446655440003'::UUID,
 'East Side Power Station',
 'power_plant',
 'critical',
 ST_SetSRID(ST_MakePoint(-74.0035, 40.7143), 4326),
 '789 Power Rd, Riverside',
 100,
 '{"capacity_mw": 250, "fuel_type": "natural_gas", "backup_generators": true}'
),
('660e8400-e29b-41d4-a716-446655440004'::UUID,
 '550e8400-e29b-41d4-a716-446655440003'::UUID,
 'Main Street Bridge',
 'bridge',
 'high',
 ST_SetSRID(ST_MakePoint(-74.0065, 40.7143), 4326),
 'Main St crossing Industrial Zone',
 50000,
 '{"year_built": 1985, "bridge_type": "steel_truss", "clearance_height": "15ft"}'
),
('660e8400-e29b-41d4-a716-446655440005'::UUID,
 '550e8400-e29b-41d4-a716-446655440004'::UUID,
 'Riverside Water Treatment',
 'water_facility',
 'critical',
 ST_SetSRID(ST_MakePoint(-74.0035, 40.7113), 4326),
 '321 River Rd, Lowland Parks',
 100,
 '{"daily_capacity_gallons": 5000000, "backup_power": true}'
);

-- Insert risk assessments
INSERT INTO risk_assessments (zone_id, time_horizon, forecast_time, risk_level, risk_factors) VALUES
-- static timestamps aligned to tests (around 2025-11-11)
('550e8400-e29b-41d4-a716-446655440001'::UUID, '6h',  '2025-11-11T06:00:00Z', 0.65, '{"precipitation": 2.3, "river_level": 3.1, "soil_saturation": 0.78}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '6h',  '2025-11-11T06:00:00Z', 0.58, '{"precipitation": 2.1, "river_level": 2.8, "soil_saturation": 0.72}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '6h',  '2025-11-11T06:00:00Z', 0.42, '{"precipitation": 1.8, "river_level": 2.2, "soil_saturation": 0.65}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '6h',  '2025-11-11T06:00:00Z', 0.71, '{"precipitation": 2.5, "river_level": 3.4, "soil_saturation": 0.82}'),

('550e8400-e29b-41d4-a716-446655440001'::UUID, '12h', '2025-11-11T12:00:00Z', 0.72, '{"precipitation": 3.1, "river_level": 3.8, "soil_saturation": 0.85}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '12h', '2025-11-11T12:00:00Z', 0.68, '{"precipitation": 2.9, "river_level": 3.5, "soil_saturation": 0.80}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '12h', '2025-11-11T12:00:00Z', 0.55, '{"precipitation": 2.4, "river_level": 2.9, "soil_saturation": 0.72}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '12h', '2025-11-11T12:00:00Z', 0.78, '{"precipitation": 3.3, "river_level": 4.1, "soil_saturation": 0.88}'),

('550e8400-e29b-41d4-a716-446655440001'::UUID, '24h', '2025-11-12T00:00:00Z', 0.81, '{"precipitation": 4.2, "river_level": 4.8, "soil_saturation": 0.92}'),
('550e8400-e29b-41d4-a716-446655440002'::UUID, '24h', '2025-11-12T00:00:00Z', 0.76, '{"precipitation": 3.8, "river_level": 4.3, "soil_saturation": 0.88}'),
('550e8400-e29b-41d4-a716-446655440003'::UUID, '24h', '2025-11-12T00:00:00Z', 0.63, '{"precipitation": 3.1, "river_level": 3.6, "soil_saturation": 0.78}'),
('550e8400-e29b-41d4-a716-446655440004'::UUID, '24h', '2025-11-12T00:00:00Z', 0.85, '{"precipitation": 4.5, "river_level": 5.2, "soil_saturation": 0.95}');

-- Insert damage assessments
INSERT INTO damage_assessments (asset_id, assessment_time, damage_level, damage_type, estimated_cost, status, notes) VALUES
('660e8400-e29b-41d4-a716-446655440001'::UUID, NOW() - INTERVAL '2 hours', 0.15, 'water_damage', 45000, 'assessed', 'Minor flooding in basement, equipment needs drying'),
('660e8400-e29b-41d4-a716-446655440003'::UUID, NOW() - INTERVAL '4 hours', 0.25, 'electrical_damage', 120000, 'under_repair', 'Transformer damaged due to water exposure'),
('660e8400-e29b-41d4-a716-446655440004'::UUID, NOW() - INTERVAL '1 hour', 0.10, 'structural', 25000, 'assessed', 'Minor erosion around bridge supports');

-- Insert resources
INSERT INTO resources (id, code, name, type, status, location, capacity, capabilities, contact_info) VALUES
('770e8400-e29b-41d4-a716-446655440001'::UUID,
 'D-001',
 'Central Depot',
 'depot',
 'available',
 ST_SetSRID(ST_MakePoint(-74.0040, 40.7140), 4326),
 NULL,
 '{"address": "123 Depot Rd", "capacity_units": 50}',
 '{"phone": "555-0100", "radio": "Channel 0"}'
),
('770e8400-e29b-41d4-a716-446655440002'::UUID,
 'P-001',
 'High-Capacity Pump',
 'equipment',
 'available',
 ST_SetSRID(ST_MakePoint(-74.0060, 40.7130), 4326),
 8,
 '{"type": "pump", "subtype": "portable", "capacity_lps": 1200, "units": 4, "depot": "D-001"}',
 '{"phone": "555-0102", "radio": "Channel 2"}'
),
('770e8400-e29b-41d4-a716-446655440003'::UUID,
 'S-001',
 'Sandbag Stockpile',
 'equipment',
 'available',
 ST_SetSRID(ST_MakePoint(-74.0050, 40.7120), 4326),
 6,
 '{"type": "sandbags", "subtype": "bulk", "units": 5000, "depot": "D-001"}',
 '{"phone": "555-0105"}'
),
('770e8400-e29b-41d4-a716-446655440004'::UUID,
 'V-001',
 'High-Water Vehicle',
 'equipment',
 'deployed',
 ST_SetSRID(ST_MakePoint(-74.0070, 40.7150), 4326),
 4,
 '{"type": "vehicle", "subtype": "high-water", "units": 2, "depot": "D-001"}',
 '{"phone": "555-0106"}'
),
('770e8400-e29b-41d4-a716-446655440005'::UUID,
 'C-ALPHA',
 'Emergency Response Team Alpha',
 'crew',
 'ready',
 ST_SetSRID(ST_MakePoint(-74.0045, 40.7135), 4326),
 12,
 '{"skills": ["search_rescue", "medical_aid", "evacuation"], "depot": "D-001"}',
 '{"phone": "555-0101", "radio": "Channel 1", "email": "team-alpha@emergency.gov"}'
),
('770e8400-e29b-41d4-a716-446655440006'::UUID,
 'C-MED',
 'Medical Response Team',
 'crew',
 'available',
 ST_SetSRID(ST_MakePoint(-74.0055, 40.7125), 4326),
 6,
 '{"skills": ["emergency_medical", "triage", "patient_transport"], "depot": "D-001"}',
 '{"phone": "555-0103", "radio": "Channel 3"}'
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
('880e8400-e29b-41d4-a716-446655440001'::UUID,
 'GAUGE-MAIN-01',
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
('880e8400-e29b-41d4-a716-446655440002'::UUID,
 'GAUGE-IND-01',
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
('880e8400-e29b-41d4-a716-446655440003'::UUID,
 'GAUGE-LOW-01',
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

-- Mississippi River focus gauges
INSERT INTO gauges (id, code, name, location, river_name, gauge_type, unit, alert_threshold, warning_threshold, status, metadata) VALUES
('691e9435-6617-4fcf-bddd-f83dcf9ed5d0'::UUID,
 '07010000',
 'Mississippi R. at St. Louis, MO',
 ST_SetSRID(ST_MakePoint(-90.17978, 38.62900), 4326),
 'Mississippi River',
 'water_level',
 'feet',
 9.144,  -- 30 ft flood stage
 8.5344, -- 28 ft action stage
 'active',
 '{"usgs_id":"07010000","unit_display":"ft","stages_ft":{"action":28,"flood":30,"moderate":35,"major":40}}'
),
('fbb9d041-499e-47bd-91bb-19ecf1647101'::UUID,
 '05587450',
 'Mississippi R. at Grafton, IL',
 ST_SetSRID(ST_MakePoint(-90.42899, 38.96797), 4326),
 'Mississippi River',
 'water_level',
 'feet',
 8.8392, -- 29 ft
 8.2296, -- 27 ft
 'active',
 '{"usgs_id":"05587450","unit_display":"ft","stages_ft":{"action":27,"flood":29}}'
),
('0da84cd0-3d8c-4d87-b186-3d92fe2571dd'::UUID,
 '06934500',
 'Missouri R. at Hermann, MO',
 ST_SetSRID(ST_MakePoint(-91.43850, 38.70981), 4326),
 'Missouri River',
 'water_level',
 'feet',
 8.5344, -- 28 ft
 7.9248, -- 26 ft
 'active',
 '{"usgs_id":"06934500","unit_display":"ft","stages_ft":{"action":26,"flood":28}}'
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

-- St. Louis corridor readings (feet stored as meters)
INSERT INTO gauge_readings (gauge_id, reading_value, reading_time, quality_flag, metadata) VALUES
('691e9435-6617-4fcf-bddd-f83dcf9ed5d0'::UUID, 7.4676, NOW() - INTERVAL '30 minutes', 'good', '{"unit":"ft","value_ft":24.5}'),
('691e9435-6617-4fcf-bddd-f83dcf9ed5d0'::UUID, 7.62,   NOW() - INTERVAL '10 minutes', 'good', '{"unit":"ft","value_ft":25.0}'),
('691e9435-6617-4fcf-bddd-f83dcf9ed5d0'::UUID, 7.7724, NOW() - INTERVAL '2 minutes',  'good', '{"unit":"ft","value_ft":25.5}'),

('fbb9d041-499e-47bd-91bb-19ecf1647101'::UUID, 7.1323, NOW() - INTERVAL '28 minutes', 'good', '{"unit":"ft","value_ft":23.4}'),
('fbb9d041-499e-47bd-91bb-19ecf1647101'::UUID, 7.2847, NOW() - INTERVAL '12 minutes', 'good', '{"unit":"ft","value_ft":23.9}'),
('fbb9d041-499e-47bd-91bb-19ecf1647101'::UUID, 7.4066, NOW() - INTERVAL '3 minutes',  'good', '{"unit":"ft","value_ft":24.3}'),

('0da84cd0-3d8c-4d87-b186-3d92fe2571dd'::UUID, 6.9494, NOW() - INTERVAL '26 minutes', 'good', '{"unit":"ft","value_ft":22.8}'),
('0da84cd0-3d8c-4d87-b186-3d92fe2571dd'::UUID, 7.1018, NOW() - INTERVAL '11 minutes', 'good', '{"unit":"ft","value_ft":23.3}'),
('0da84cd0-3d8c-4d87-b186-3d92fe2571dd'::UUID, 7.2238, NOW() - INTERVAL '3 minutes',  'good', '{"unit":"ft","value_ft":23.7}');

-- Normalize gauge codes to match UI/tests pattern
UPDATE gauges SET code = CASE WHEN code LIKE 'G-%' THEN code ELSE 'G-' || code END;

-- Insert response plans
INSERT INTO response_plans (name, description, plan_type, trigger_conditions, recommended_actions, required_resources, estimated_duration, priority, status) VALUES
(
 'Urban Flood Evacuation Plan',
 'Standard operating procedure for evacuating urban residential areas during flood events',
 'evacuation',
 '{"water_level_threshold": 3.5, "rainfall_rate": "1in/hr", "forecast_confidence": 0.8}',
 '["Issue evacuation orders", "Open emergency shelters", "Deploy transport resources", "Establish traffic control", "Coordinate with law enforcement"]',
 '{"crews": 4, "vehicles": 12, "facilities": 2, "equipment": ["boats", "buses", "communications"]}',
 8,
 'high',
 'active'
),
(
 'Infrastructure Protection Protocol',
 'Protect critical infrastructure from flood damage',
 'infrastructure_protection',
 '{"water_level_threshold": 2.8, "lead_time_hours": 6}',
 '["Deploy flood barriers", "Pump out critical facilities", "Shut down non-essential systems", "Backup critical data", "Staff emergency generators"]',
 '{"crews": 3, "vehicles": 8, "equipment": ["pumps", "sandbags", "generators", "fuel"]}',
 12,
 'critical',
 'active'
),
(
 'Rapid Resource Deployment',
 'Quick deployment of emergency resources to affected areas',
 'resource_deployment',
 '{"alert_severity": "high", "affected_population": 100}',
 '["Assess resource needs", "Deploy nearest available resources", "Establish command post", "Coordinate with other agencies"]',
 '{"crews": 2, "vehicles": 6, "equipment": ["command_vehicle", "communications", "medical_supplies"]}',
 4,
 'medium',
 'active'
);

-- Add a test-friendly plan with assignments
INSERT INTO response_plans (id, name, version, description, plan_type, trigger_conditions, recommended_actions, required_resources, assignments, coverage, notes, estimated_duration, priority, status)
VALUES (
  'a70e8400-e29b-41d4-a716-446655440001'::UUID,
  'Flood Response Alpha',
  '1.0',
  'Test response plan for automated validation',
  'resource_deployment',
  '{"river_level_gt":4.0}',
  '["Deploy pumps", "Open shelters"]',
  '{"pumps":4,"crews":2}',
  '[{"zoneId":"Z-DOWNTOWN","priority":1,"actions":[{"type":"deploy","equipment":"P-001","qty":2}]}, {"zoneId":"Z-RIVERSIDE","priority":2,"actions":[{"type":"deploy","equipment":"S-001","qty":1}]}]',
  '{"total_zones":4,"covered_zones":2,"coverage_percentage":50}',
  'Auto-generated for tests',
  24,
  'high',
  'active'
);

COMMIT;

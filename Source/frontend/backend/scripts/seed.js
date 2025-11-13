#!/usr/bin/env node

/**
 * Database Seed Script
 *
 * This script seeds the database with sample data for development and testing.
 */

import pkg from 'pg';
import { fileURLToPath } from 'url';

const { Pool } = pkg;

const __filename = fileURLToPath(import.meta.url);

// Database connection configuration
const config = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5433,
  database: process.env.DB_NAME || 'flood_prediction',
  user: process.env.DB_USER || 'flood_user',
  password: process.env.DB_PASSWORD || 'flood_password',
};

console.log('🌱 Flood Prediction Database Seeder');
console.log('====================================');

async function connectToDatabase() {
  console.log(`\n📡 Connecting to PostgreSQL...`);
  console.log(`   Host: ${config.host}:${config.port}`);
  console.log(`   Database: ${config.database}`);

  const pool = new Pool(config);

  try {
    const client = await pool.connect();
    console.log('✅ Database connection successful');
    return pool;
  } catch (error) {
    console.error('❌ Database connection failed:', error.message);
    process.exit(1);
  }
}

async function seedSampleData(pool) {
  console.log('\n🌱 Seeding sample data...');

  try {
    // Sample zones data
    await pool.query(`
      INSERT INTO zones (id, name, description, population, area_km2, geometry) VALUES
      ('00000000-0000-0000-0000-000000000001', 'Riverside North', 'Northern riverside residential area', 12450, 15.2,
       ST_GeomFromText('POLYGON((-3.71 40.41, -3.70 40.41, -3.70 40.42, -3.71 40.42, -3.71 40.41))', 4326)),
      ('00000000-0000-0000-0000-000000000002', 'Industrial District', 'Commercial and industrial zone', 8200, 12.8,
       ST_GeomFromText('POLYGON((-3.69 40.41, -3.68 40.41, -3.68 40.42, -3.69 40.42, -3.69 40.41))', 4326)),
      ('00000000-0000-0000-0000-000000000003', 'Downtown Central', 'Central business district', 15600, 8.5,
       ST_GeomFromText('POLYGON((-3.70 40.40, -3.69 40.40, -3.69 40.41, -3.70 40.41, -3.70 40.40))', 4326)),
      ('00000000-0000-0000-0000-000000000004', 'Residential Heights', 'Elevated residential area', 9800, 18.3,
       ST_GeomFromText('POLYGON((-3.71 40.40, -3.70 40.40, -3.70 40.41, -3.71 40.41, -3.71 40.40))', 4326))
      ON CONFLICT (id) DO NOTHING
    `);

    // Sample assets data
    await pool.query(`
      INSERT INTO assets (id, zone_id, name, type, criticality, location, address, capacity, metadata) VALUES
      ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Hospital HN1', 'hospital', 'critical',
       ST_GeomFromText('POINT(-3.705 40.415)', 4326), '123 Riverside Ave', 200, '{"emergency_services": true, "floors": 5}'),
      ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'School SN3', 'school', 'high',
       ST_GeomFromText('POINT(-3.708 40.418)', 4326), '456 North St', 500, '{"type": "elementary", "floors": 2}'),
      ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000002', 'Power Plant PP1', 'power_plant', 'critical',
       ST_GeomFromText('POINT(-3.685 40.415)', 4326), '789 Industrial Way', 1, '{"capacity_mw": 500, "type": "gas"}'),
      ('10000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000002', 'Water Treatment WT1', 'water_treatment', 'critical',
       ST_GeomFromText('POINT(-3.688 40.418)', 4326), '321 Treatment Rd', 1, '{"capacity_mgd": 50}'),
      ('10000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000003', 'City Hall', 'government', 'high',
       ST_GeomFromText('POINT(-3.695 40.405)', 4326), '1 City Square', 100, '{"floors": 4, "emergency_ops": true}')
      ON CONFLICT (id) DO NOTHING
    `);

    // Sample risk assessments
    const forecastTime = new Date();
    const timeHorizons = ['6h', '12h', '18h', '24h', '48h', '72h'];

    for (const horizon of timeHorizons) {
      for (let i = 1; i <= 4; i++) {
        const zoneId = `00000000-0000-0000-0000-00000000000${i}`;
        const riskLevel = Math.random() * 0.8 + 0.1; // 0.1 to 0.9

        await pool.query(`
          INSERT INTO risk_assessments (zone_id, time_horizon, forecast_time, risk_level, risk_factors)
          VALUES ($1, $2, $3, $4, $5)
          ON CONFLICT DO NOTHING
        `, [
          zoneId,
          horizon,
          forecastTime,
          riskLevel,
          JSON.stringify({
            precipitation: Math.random() * 50,
            riverLevel: Math.random() * 10,
            soilSaturation: Math.random() * 100,
            temperature: Math.random() * 15 + 10
          })
        ]);
      }
    }

    // Sample resources
    await pool.query(`
      INSERT INTO resources (id, name, type, status, location, capacity, capabilities, contact_info) VALUES
      ('20000000-0000-0000-0000-000000000001', 'Emergency Team Alpha', 'emergency_crew', 'available',
       ST_GeomFromText('POINT(-3.695 40.405)', 4326), 12, '["medical", "rescue", "evacuation"]', '{"phone": "+1-555-0001", "email": "alpha@emergency.gov"}'),
      ('20000000-0000-0000-0000-000000000002', 'Fire Station Central', 'fire_crew', 'available',
       ST_GeomFromText('POINT(-3.692 40.408)', 4326), 8, '["fire_suppression", "hazardous_materials"]', '{"phone": "+1-555-0002", "email": "central@fire.gov"}'),
      ('20000000-0000-0000-0000-000000000003', 'Engineering Unit Beta', 'engineering_crew', 'deployed',
       ST_GeomFromText('POINT(-3.705 40.415)', 4326), 6, '["infrastructure", "utilities", "debris_removal"]', '{"phone": "+1-555-0003", "email": "beta@engineering.gov"}'),
      ('20000000-0000-0000-0000-000000000004', 'Medical Response Team', 'medical_crew', 'standby',
       ST_GeomFromText('POINT(-3.698 40.402)', 4326), 10, '["emergency_medical", "triage", "evacuation_support"]', '{"phone": "+1-555-0004", "email": "medical@health.gov"}')
      ON CONFLICT (id) DO NOTHING
    `);

    // Sample alerts
    await pool.query(`
      INSERT INTO alerts (id, zone_id, severity, alert_type, title, message, acknowledged, metadata) VALUES
      ('30000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'high', 'flood_warning', 'Flood Warning - Riverside North', 'River levels rising rapidly. Prepare for possible evacuation.', false, '{"source": "river_gauge", "threshold_exceeded": true}'),
      ('30000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002', 'medium', 'infrastructure', 'Power Outage Reported', 'Power Plant PP1 experiencing issues. Backup systems activated.', true, '{"acknowledged_by": "operator1", "acknowledged_at": "2025-11-13T10:00:00Z"}'),
      ('30000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000003', 'low', 'information', 'Emergency Services on Standby', 'All emergency crews are on standby due to weather conditions.', false, '{"priority": "information_only"}'),
      ('30000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000004', 'medium', 'weather', 'Heavy Rainfall Expected', 'Heavy rainfall expected in the next 6 hours. Monitor conditions closely.', false, '{"precipitation_mm": 45, "duration_hours": 6}')
      ON CONFLICT (id) DO NOTHING
    `);

    console.log('✅ Sample data seeded successfully');

  } catch (error) {
    console.error('❌ Seeding failed:', error.message);
    throw error;
  }
}

async function main() {
  let pool = null;

  try {
    // Connect to database
    pool = await connectToDatabase();

    // Seed sample data
    await seedSampleData(pool);

    console.log('\n🎉 Database seeding completed successfully!');
    console.log('\n🚀 You can now start the backend server:');
    console.log('   cd backend && npm start');

  } catch (error) {
    console.error('\n❌ Database seeding script failed:', error.message);
    process.exit(1);
  } finally {
    if (pool) {
      await pool.end();
      console.log('\n🔐 Database connection closed');
    }
  }
}

// Handle script termination gracefully
process.on('SIGINT', () => {
  console.log('\n\n⚠️  Seeding script interrupted by user');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n\n⚠️  Seeding script terminated');
  process.exit(0);
});

// Run the script
main().catch(console.error);
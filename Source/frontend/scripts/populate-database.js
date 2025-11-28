#!/usr/bin/env node

/**
 * Database Populate Script
 *
 * This script populates the PostgreSQL database with demo data for the flood prediction system.
 * It can be run independently or as part of the Docker initialization.
 */

import pkg from 'pg';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const { Pool } = pkg;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Database connection configuration
const config = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5433,
  database: process.env.DB_NAME || 'flood_prediction',
  user: process.env.DB_USER || 'flood_user',
  password: process.env.DB_PASSWORD || 'flood_password',
};

console.log('🌊 Flood Prediction Database Populate Script');
console.log('==========================================');

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

async function executeSQLFile(pool, filename, description) {
  console.log(`\n📄 ${description}`);
  console.log(`   File: ${filename}`);

  try {
    const sqlPath = path.join(__dirname, '..', 'database', 'init', filename);
    const sql = fs.readFileSync(sqlPath, 'utf8');

    await pool.query(sql);
    console.log(`✅ ${description} completed successfully`);
  } catch (error) {
    console.error(`❌ ${description} failed:`, error.message);
    throw error;
  }
}

async function verifyDataPopulation(pool) {
  console.log('\n🔍 Verifying data population...');

  const checks = [
    {
      name: 'Zones',
      query: 'SELECT COUNT(*) as count FROM zones',
      expected: 4
    },
    {
      name: 'Assets',
      query: 'SELECT COUNT(*) as count FROM assets',
      expected: 5
    },
    {
      name: 'Risk Assessments',
      query: 'SELECT COUNT(*) as count FROM risk_assessments',
      expected: 16
    },
    {
      name: 'Resources',
      query: 'SELECT COUNT(*) as count FROM resources',
      expected: 4
    },
    {
      name: 'Alerts',
      query: 'SELECT COUNT(*) as count FROM alerts',
      expected: 4
    },
    {
      name: 'Communications',
      query: 'SELECT COUNT(*) as count FROM communications',
      expected: 5
    },
    {
      name: 'Gauges',
      query: 'SELECT COUNT(*) as count FROM gauges',
      expected: 3
    },
    {
      name: 'Gauge Readings',
      query: 'SELECT COUNT(*) as count FROM gauge_readings',
      expected: 15
    },
    {
      name: 'Response Plans',
      query: 'SELECT COUNT(*) as count FROM response_plans',
      expected: 3
    },
    {
      name: 'Damage Assessments',
      query: 'SELECT COUNT(*) as count FROM damage_assessments',
      expected: 3
    }
  ];

  let allChecksPassed = true;

  for (const check of checks) {
    try {
      const result = await pool.query(check.query);
      const count = parseInt(result.rows[0].count);

      if (count === check.expected) {
        console.log(`✅ ${check.name}: ${count} records`);
      } else {
        console.log(`⚠️  ${check.name}: ${count} records (expected ${check.expected})`);
        allChecksPassed = false;
      }
    } catch (error) {
      console.log(`❌ ${check.name}: Failed to check - ${error.message}`);
      allChecksPassed = false;
    }
  }

  if (allChecksPassed) {
    console.log('\n🎉 All data verification checks passed!');
  } else {
    console.log('\n⚠️  Some verification checks failed');
  }
}

async function showSampleData(pool) {
  console.log('\n📊 Sample Data Preview:');
  console.log('=======================');

  try {
    // Sample zones
    const zones = await pool.query('SELECT name, population FROM zones ORDER BY name LIMIT 2');
    console.log('\n🗺️  Zones:');
    zones.rows.forEach(zone => {
      console.log(`   • ${zone.name} - Population: ${zone.population.toLocaleString()}`);
    });

    // Sample assets
    const assets = await pool.query('SELECT name, type, criticality FROM assets ORDER BY criticality DESC LIMIT 3');
    console.log('\n🏢 Critical Assets:');
    assets.rows.forEach(asset => {
      console.log(`   • ${asset.name} (${asset.type}) - ${asset.criticality} priority`);
    });

    // Sample alerts
    const alerts = await pool.query('SELECT severity, title FROM alerts ORDER BY created_at DESC LIMIT 3');
    console.log('\n🚨 Recent Alerts:');
    alerts.rows.forEach(alert => {
      console.log(`   • [${alert.severity.toUpperCase()}] ${alert.title}`);
    });

    // Sample risk assessments
    const risk = await pool.query(`
      SELECT ra.risk_level, z.name as zone_name
      FROM risk_assessments ra
      JOIN zones z ON ra.zone_id = z.id
      WHERE ra.time_horizon = '12h'
      ORDER BY ra.risk_level DESC
      LIMIT 3
    `);
    console.log('\n⚠️  Current Risk Levels (12h forecast):');
    risk.rows.forEach(item => {
      console.log(`   • ${item.zone_name}: ${(item.risk_level * 100).toFixed(1)}%`);
    });

  } catch (error) {
    console.log(`❌ Failed to fetch sample data: ${error.message}`);
  }
}

async function main() {
  let pool = null;

  try {
    // Connect to database
    pool = await connectToDatabase();

    // Execute schema and data files
    await executeSQLFile(pool, '01-schema.sql', 'Creating database schema');
    await executeSQLFile(pool, '02-migrate-mock-data.sql', 'Migrating mock data');

    // Verify data population
    await verifyDataPopulation(pool);

    // Show sample data
    await showSampleData(pool);

    console.log('\n🎯 Database populate script completed successfully!');
    console.log('\n🚀 You can now start the API server:');
    console.log('   cd backend && node server.js');
    console.log('\n🌐 Or use Docker Compose:');
    console.log('   docker compose up -d');

  } catch (error) {
    console.error('\n❌ Database populate script failed:', error.message);
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
  console.log('\n\n⚠️  Script interrupted by user');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n\n⚠️  Script terminated');
  process.exit(0);
});

// Run the script
main().catch(console.error);

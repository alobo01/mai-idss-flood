#!/usr/bin/env node

/**
 * Database Migration Script
 *
 * This script runs database migrations for the flood prediction system.
 * It reads migration files from database/migrations directory.
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

console.log('🗄️  Flood Prediction Database Migration');
console.log('======================================');

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

async function runMigrations(pool) {
  console.log('\n🚀 Running database migrations...');

  try {
    // Ensure migrations table exists
    await pool.query(`
      CREATE TABLE IF NOT EXISTS migrations (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      )
    `);

    // Get list of migration files
    const migrationsDir = path.join(__dirname, '..', '..', 'database', 'migrations');

    if (!fs.existsSync(migrationsDir)) {
      console.log('📁 No migrations directory found, skipping migrations');
      return;
    }

    const migrationFiles = fs.readdirSync(migrationsDir)
      .filter(file => file.endsWith('.sql'))
      .sort();

    // Get executed migrations
    const executedResult = await pool.query('SELECT filename FROM migrations');
    const executedFiles = new Set(executedResult.rows.map(row => row.filename));

    // Run pending migrations
    for (const file of migrationFiles) {
      if (!executedFiles.has(file)) {
        console.log(`   📄 Running migration: ${file}`);

        const migrationSQL = fs.readFileSync(path.join(migrationsDir, file), 'utf8');

        const client = await pool.connect();
        try {
          await client.query('BEGIN');
          await client.query(migrationSQL);
          await client.query('INSERT INTO migrations (filename) VALUES ($1)', [file]);
          await client.query('COMMIT');
          console.log(`   ✅ Migration ${file} completed successfully`);
        } catch (error) {
          await client.query('ROLLBACK');
          throw error;
        } finally {
          client.release();
        }
      } else {
        console.log(`   ⏭️  Migration ${file} already executed`);
      }
    }

    console.log('\n🎉 All migrations completed successfully!');

  } catch (error) {
    console.error('\n❌ Migration failed:', error.message);
    throw error;
  }
}

async function main() {
  let pool = null;

  try {
    // Connect to database
    pool = await connectToDatabase();

    // Run migrations
    await runMigrations(pool);

    console.log('\n🎯 Database migration script completed successfully!');

  } catch (error) {
    console.error('\n❌ Database migration script failed:', error.message);
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
  console.log('\n\n⚠️  Migration script interrupted by user');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n\n⚠️  Migration script terminated');
  process.exit(0);
});

// Run the script
main().catch(console.error);
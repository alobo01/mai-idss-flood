#!/usr/bin/env node

/**
 * Database Seed Script
 *
 * Imports the mock JSON data (zones, alerts, resources, gauges, risk, plan, comms)
 * into the PostgreSQL/PostGIS database so every environment can operate with
 * the same dataset as the standalone mock API.
 */

import fs from 'fs';
import path from 'path';
import pkg from 'pg';
import { fileURLToPath } from 'url';

const { Pool } = pkg;

const __filename = fileURLToPath(import.meta.url);
const scriptsDir = path.dirname(__filename);
const backendDir = path.join(scriptsDir, '..');
const projectRoot = path.join(backendDir, '..');

const mockDataPaths = [
  process.env.MOCK_DATA_PATH,
  path.join(projectRoot, 'public', 'mock'),
  backendDir,
].filter(Boolean);

const config = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5433,
  database: process.env.DB_NAME || 'flood_prediction',
  user: process.env.DB_USER || 'flood_user',
  password: process.env.DB_PASSWORD || 'flood_password',
};

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const severityMap = {
  severe: 'critical',
  critical: 'critical',
  high: 'high',
  moderate: 'medium',
  medium: 'medium',
  low: 'low',
  operational: 'medium',
};

const trendLabels = {
  rising: 'rising',
  steady: 'steady',
  falling: 'falling',
};

const makeRecencyGenerator = (spacingMinutes = 30) => {
  const anchor = Date.now();
  let counter = 0;
  return () => {
    const timestamp = new Date(anchor - counter * spacingMinutes * 60 * 1000).toISOString();
    counter += 1;
    return timestamp;
  };
};

const readJson = (filename) => {
  for (const dir of mockDataPaths) {
    const candidate = path.join(dir, filename);
    if (fs.existsSync(candidate)) {
      const content = fs.readFileSync(candidate, 'utf8');
      return JSON.parse(content);
    }
  }
  return null;
};

const listMockFiles = (pattern) => {
  for (const dir of mockDataPaths) {
    if (dir && fs.existsSync(dir)) {
      return fs.readdirSync(dir).filter((file) => pattern.test(file)).map((file) => ({
        name: file,
        path: path.join(dir, file),
      }));
    }
  }
  return [];
};

const toIso = (value) => {
  if (!value) return new Date().toISOString();
  if (value.includes('T') && value.includes('-') && value.includes('Z') && value.indexOf('T') < value.lastIndexOf('-')) {
    const [datePart, timePartRaw] = value.split('T');
    const timePart = timePartRaw.replace(/-/g, ':');
    const normalized = `${datePart}T${timePart}`;
    return normalized;
  }
  return value;
};

const connect = async () => {
  console.log('📡 Connecting to PostgreSQL...');
  const pool = new Pool(config);
  const client = await pool.connect();
  console.log('✅ Connected\n');
  return { pool, client };
};

const upsertZones = async (client) => {
  const geoJson = readJson('zones.geojson');
  if (!geoJson?.features) {
    throw new Error('zones.geojson not found. Set MOCK_DATA_PATH or keep the default dataset in public/mock.');
  }

  console.log(`• Importing ${geoJson.features.length} zones`);
  const zoneMap = new Map();

  for (const feature of geoJson.features) {
    const props = feature.properties || {};
    const code = props.id;
    if (!code) {
      console.warn('  ↳ Skipping zone without id');
      continue;
    }

    const result = await client.query(
      `
        INSERT INTO zones (code, name, description, population, area_km2, admin_level, critical_assets, geometry)
        VALUES ($1, $2, $3, $4, $5, $6, $7,
          ST_GeomFromGeoJSON($8)
        )
        ON CONFLICT (code)
        DO UPDATE SET
          name = EXCLUDED.name,
          description = EXCLUDED.description,
          population = EXCLUDED.population,
          area_km2 = EXCLUDED.area_km2,
          admin_level = EXCLUDED.admin_level,
          critical_assets = EXCLUDED.critical_assets,
          geometry = EXCLUDED.geometry
        RETURNING id
      `,
      [
        code,
        props.name || code,
        props.description || `Zone ${props.name || code}`,
        props.population || 0,
        props.area_km2 || feature.properties?.area || 0,
        props.admin_level || 10,
        props.critical_assets || [],
        JSON.stringify(feature.geometry),
      ],
    );

    zoneMap.set(code, result.rows[0].id);
  }

  return zoneMap;
};

const resetTables = async (client) => {
  console.log('• Resetting dependent tables');
  await client.query('TRUNCATE TABLE deployments, gauge_readings RESTART IDENTITY CASCADE');
  await client.query('TRUNCATE TABLE alerts, communications, risk_assessments, gauges, response_plans, damage_assessments RESTART IDENTITY CASCADE');
  await client.query('DELETE FROM resources');
  await client.query('DELETE FROM assets');
};

const upsertAssets = async (client, zoneMap) => {
  const assets = readJson('assets.json');
  if (!assets?.length) {
    console.warn('  ↳ assets.json missing, skipping asset import');
    return;
  }

  console.log(`• Importing ${assets.length} critical assets`);

  for (const asset of assets) {
    const zoneCode = asset.zoneId || asset.zoneCode;
    const zoneUuid = asset.zoneUuid || (zoneCode ? zoneMap.get(zoneCode) : null);
    if (!zoneUuid) {
      console.warn(`  ↳ Skipping asset "${asset.name}" - unknown zone ${zoneCode || '(missing)'}`);
      continue;
    }

    const lat = Number(asset.lat);
    const lng = Number(asset.lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      console.warn(`  ↳ Skipping asset "${asset.name}" - invalid coordinates`);
      continue;
    }

    const criticality = (asset.criticality || 'medium').toString().toLowerCase();
    const allowedCriticality = ['low', 'medium', 'high', 'critical'];
    const normalizedCriticality = allowedCriticality.includes(criticality) ? criticality : 'medium';

    const metadata = { ...(asset.metadata || {}) };
    if (asset.code) {
      metadata.code = asset.code;
    }
    if (!metadata.externalId) {
      metadata.externalId = asset.externalId || asset.shortId || asset.code || null;
      if (!metadata.externalId && zoneCode) {
        metadata.externalId = `${zoneCode}-${(asset.type || 'asset').toString().toLowerCase()}`;
      }
    }
    if (!metadata.externalId) {
      delete metadata.externalId;
    }

    const params = [
      uuidPattern.test(asset.id || '') ? asset.id : null,
      zoneUuid,
      asset.name || 'Critical Asset',
      (asset.type || 'facility').toString().toLowerCase(),
      normalizedCriticality,
      lng,
      lat,
      asset.address || null,
      typeof asset.capacity === 'number' ? asset.capacity : null,
      JSON.stringify(metadata || {}),
    ];

    await client.query(
      `
        INSERT INTO assets (id, zone_id, name, type, criticality, location, address, capacity, metadata)
        VALUES (
          COALESCE($1::uuid, uuid_generate_v4()),
          $2,
          $3,
          $4,
          $5,
          ST_SetSRID(ST_MakePoint($6::double precision, $7::double precision), 4326),
          $8,
          $9,
          COALESCE($10::jsonb, '{}'::jsonb)
        )
        ON CONFLICT (id)
        DO UPDATE SET
          name = EXCLUDED.name,
          type = EXCLUDED.type,
          criticality = EXCLUDED.criticality,
          location = EXCLUDED.location,
          address = EXCLUDED.address,
          capacity = EXCLUDED.capacity,
          metadata = EXCLUDED.metadata
      `,
      params,
    );
  }
};

const upsertResources = async (client) => {
  const resourcesJson = readJson('resources.json');
  if (!resourcesJson) {
    console.warn('  ↳ resources.json missing, skipping resource import');
    return;
  }

  const toPointParams = (item) => ({
    lng: typeof item.lng === 'number' ? item.lng : null,
    lat: typeof item.lat === 'number' ? item.lat : null,
  });

  const insertResource = async ({ code, name, type, status, lat, lng, capacity, capabilities }) => {
    await client.query(
      `
        INSERT INTO resources (code, name, type, status, location, capacity, capabilities, contact_info)
        VALUES (
          $1, $2, $3, $4,
          CASE
            WHEN $5::double precision IS NULL OR $6::double precision IS NULL THEN NULL
            ELSE ST_SetSRID(ST_MakePoint($5::double precision, $6::double precision), 4326)
          END,
          $7,
          $8::jsonb,
          '{}'::jsonb
        )
        ON CONFLICT (code)
        DO UPDATE SET
          name = EXCLUDED.name,
          type = EXCLUDED.type,
          status = EXCLUDED.status,
          location = EXCLUDED.location,
          capacity = EXCLUDED.capacity,
          capabilities = EXCLUDED.capabilities
      `,
      [code, name, type, status, lng, lat, capacity, JSON.stringify(capabilities || {})],
    );
  };

  console.log('• Importing depots, equipment, and crews');

  for (const depot of resourcesJson.depots || []) {
    const { lat, lng } = toPointParams(depot);
    await insertResource({
      code: depot.id,
      name: depot.name,
      type: 'depot',
      status: 'available',
      lat,
      lng,
      capacity: depot.capacity ?? null,
      capabilities: { lat, lng },
    });
  }

  for (const equipment of resourcesJson.equipment || []) {
    const depot = resourcesJson.depots?.find((d) => d.id === equipment.depot);
    const { lat, lng } = toPointParams(depot || {});
    await insertResource({
      code: equipment.id,
      name: `${equipment.type} ${equipment.id}`,
      type: 'equipment',
      status: equipment.status || 'available',
      lat,
      lng,
      capacity: equipment.capacity_lps || equipment.units || null,
      capabilities: {
        type: equipment.type,
        subtype: equipment.subtype,
        capacity_lps: equipment.capacity_lps,
        units: equipment.units,
        depot: equipment.depot,
      },
    });
  }

  for (const crew of resourcesJson.crews || []) {
    await insertResource({
      code: crew.id,
      name: crew.name,
      type: 'crew',
      status: crew.status || 'ready',
      lat: crew.lat,
      lng: crew.lng,
      capacity: crew.skills?.length || null,
      capabilities: {
        skills: crew.skills || [],
        depot: crew.depot,
      },
    });
  }
};

const upsertRiskAssessments = async (client, zoneMap) => {
  const riskFiles = listMockFiles(/^risk_.+\.json$/i);
  if (riskFiles.length === 0) {
    console.warn('  ↳ No risk_*.json files found, skipping risk import');
    return;
  }

  console.log(`• Importing risk assessments from ${riskFiles.length} files`);

  for (const file of riskFiles) {
    const raw = fs.readFileSync(file.path, 'utf8');
    const entries = JSON.parse(raw);

    const timestampMatch = file.name.match(/risk_(.+)\.json/i);
    const timestampRaw = timestampMatch ? timestampMatch[1] : new Date().toISOString();
    const [datePart, timePartRaw = '00-00-00Z'] = timestampRaw.split('T');
    const hourMatch = timePartRaw.match(/^(\d{2})-/);
    const horizon = hourMatch ? `${hourMatch[1]}h` : '12h';
    const forecastTime = toIso(`${datePart}T${timePartRaw}`);

    for (const entry of entries) {
      const zoneId = zoneMap.get(entry.zoneId);
      if (!zoneId) continue;

      await client.query(
        `
          INSERT INTO risk_assessments (zone_id, time_horizon, forecast_time, risk_level, risk_factors)
          VALUES ($1, $2, $3, $4, $5::jsonb)
          ON CONFLICT (zone_id, time_horizon, forecast_time)
          DO UPDATE SET
            risk_level = EXCLUDED.risk_level,
            risk_factors = EXCLUDED.risk_factors
        `,
        [zoneId, horizon, forecastTime, entry.risk, JSON.stringify(entry.drivers || [])],
      );
    }
  }
};

const upsertAlerts = async (client, zoneMap) => {
  const alerts = readJson('alerts.json');
  if (!alerts?.length) {
    console.warn('  ↳ alerts.json missing, skipping alerts import');
    return;
  }

  console.log(`• Importing ${alerts.length} alerts`);

  const alertRecency = makeRecencyGenerator(90);
  const sortedAlerts = [...alerts].sort((a, b) => {
    const aTime = Date.parse(toIso(a.timestamp)) || 0;
    const bTime = Date.parse(toIso(b.timestamp)) || 0;
    return bTime - aTime;
  });

  for (const alert of sortedAlerts) {
    const zoneId = zoneMap.get(alert.zoneId);
    if (!zoneId) continue;

    const severity = severityMap[alert.severity?.toLowerCase?.() || 'medium'] || 'medium';
    const metadata = {
      externalId: alert.id,
      crewId: alert.crewId,
      eta: alert.eta,
      status: alert.status,
      zoneCode: alert.zoneId,
    };

    const createdAt = alertRecency();

    await client.query(
      `
        INSERT INTO alerts (zone_id, severity, alert_type, title, message, acknowledged, resolved, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, false, false, $6::jsonb, $7)
      `,
      [
        zoneId,
        severity,
        (alert.type || 'system').toLowerCase(),
        alert.title,
        alert.description,
        JSON.stringify(metadata),
        createdAt,
      ],
    );
  }
};

const upsertGauges = async (client) => {
  const gauges = readJson('gauges.json');
  if (!gauges?.length) {
    console.warn('  ↳ gauges.json missing, skipping gauge import');
    return;
  }

  console.log(`• Importing ${gauges.length} gauges and readings`);

  for (const gauge of gauges) {
    const result = await client.query(
      `
        INSERT INTO gauges (code, name, location, river_name, gauge_type, unit, alert_threshold, warning_threshold, status, metadata)
        VALUES (
          $1,
          $2,
          CASE
            WHEN $3::double precision IS NULL OR $4::double precision IS NULL THEN NULL
            ELSE ST_SetSRID(ST_MakePoint($4::double precision, $3::double precision), 4326)
          END,
          $5,
          $6,
          $7,
          $8,
          $9,
          'active',
          $10::jsonb
        )
        ON CONFLICT (code)
        DO UPDATE SET
          name = EXCLUDED.name,
          location = EXCLUDED.location,
          alert_threshold = EXCLUDED.alert_threshold,
          warning_threshold = EXCLUDED.warning_threshold,
          metadata = EXCLUDED.metadata
        RETURNING id
      `,
      [
        gauge.id,
        gauge.name,
        gauge.lat,
        gauge.lng,
        gauge.river_name || 'River',
        gauge.gauge_type || 'water_level',
        gauge.unit || 'meters',
        gauge.critical_threshold ?? gauge.alert_threshold ?? 3.5,
        gauge.alert_threshold ?? gauge.warning_threshold ?? 3.0,
        JSON.stringify({ trend: gauge.trend }),
      ],
    );

    const gaugeId = result.rows[0].id;

    await client.query(
      `
        INSERT INTO gauge_readings (gauge_id, reading_value, reading_time, quality_flag, metadata)
        VALUES ($1, $2, $3, 'good', $4::jsonb)
      `,
      [gaugeId, gauge.level_m, toIso(gauge.last_updated), JSON.stringify({ trend: gauge.trend || trendLabels.steady })],
    );
  }
};

const upsertCommunications = async (client) => {
  const comms = readJson('comms.json');
  if (!comms?.length) {
    console.warn('  ↳ comms.json missing, skipping communications import');
    return;
  }

  console.log(`• Importing ${comms.length} communications`);
  const commRecency = makeRecencyGenerator(10);

  for (const comm of comms) {
    const createdAt = commRecency();

    await client.query(
      `
        INSERT INTO communications (channel, sender, recipient, message, direction, priority, status, metadata, created_at)
        VALUES ($1, $2, $3, $4, 'outbound', 'normal', 'delivered', $5::jsonb, $6)
      `,
      [
        comm.channel,
        comm.from,
        comm.channel?.startsWith('task:') ? comm.channel : 'global',
        comm.text,
        JSON.stringify({ externalId: comm.id }),
        createdAt,
      ],
    );
  }
};

const upsertPlan = async (client) => {
  const plan = readJson('plan_draft.json');
  if (!plan) {
    console.warn('  ↳ plan_draft.json missing, skipping plan import');
    return;
  }

  console.log('• Importing response plan');

  await client.query(
    `
      INSERT INTO response_plans (
        name,
        version,
        description,
        plan_type,
        trigger_conditions,
        recommended_actions,
        required_resources,
        assignments,
        coverage,
        notes,
        estimated_duration,
        priority,
        status
      )
      VALUES (
        $1,
        $2,
        $3,
        'resource_deployment',
        '{}'::jsonb,
        '[]'::jsonb,
        '{}'::jsonb,
        $4::jsonb,
        $5::jsonb,
        $6,
        8,
        'high',
        'active'
      )
    `,
    [
      plan.name || 'Mock Flood Response Plan',
      plan.version || new Date().toISOString(),
      plan.notes || 'Mock data import',
      JSON.stringify(plan.assignments || []),
      JSON.stringify(plan.coverage || {}),
      plan.notes || 'Derived from mock dataset',
    ],
  );
};

const main = async () => {
  console.log('🌱 Flood Prediction Database Seeder');
  console.log('====================================\n');

  let pool;
  let client;

  try {
    ({ pool, client } = await connect());
    await client.query('BEGIN');

    const zoneMap = await upsertZones(client);
    await resetTables(client);
    await upsertAssets(client, zoneMap);
    await upsertResources(client);
    await upsertRiskAssessments(client, zoneMap);
    await upsertAlerts(client, zoneMap);
    await upsertGauges(client);
    await upsertCommunications(client);
    await upsertPlan(client);

    await client.query('COMMIT');
    console.log('\n🎉 Mock data imported successfully!');
  } catch (error) {
    if (client) {
      await client.query('ROLLBACK');
    }
    console.error('\n❌ Seeding failed:', error);
    process.exitCode = 1;
  } finally {
    if (client) client.release();
    if (pool) await pool.end();
    console.log('\n🔐 Database connection closed');
  }
};

process.on('SIGINT', () => {
  console.log('\n⚠️  Seeding interrupted');
  process.exit(1);
});

process.on('SIGTERM', () => {
  console.log('\n⚠️  Seeding terminated');
  process.exit(1);
});

main();

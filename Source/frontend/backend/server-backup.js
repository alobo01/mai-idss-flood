import express from 'express';
import cors from 'cors';
import pkg from 'pg';
import dotenv from 'dotenv';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { fileURLToPath } from 'url';
import { swaggerUi, specs, swaggerUiOptions } from './swagger-config.js';

const { Pool } = pkg;

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 8080;

// PostgreSQL connection pool
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'flood_prediction',
  user: process.env.DB_USER || 'flood_user',
  password: process.env.DB_PASSWORD || 'flood_password',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

app.use(cors());
app.use(express.json());

// Swagger UI routes
app.use('/api-docs', swaggerUi.serve);
app.get('/api-docs', swaggerUi.setup(specs, swaggerUiOptions));

// OpenAPI JSON endpoint
app.get('/api/openapi.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(specs);
});

/**
 * @swagger
 * /health:
 *   get:
 *     tags:
 *       - Health
 *     summary: Health check
 *     description: Check API health and database connectivity
 *     responses:
 *       200:
 *         description: System is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   enum: [ok, error]
 *                   example: ok
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 database:
 *                   type: string
 *                   enum: [connected, disconnected]
 *                 version:
 *                   type: string
 *                   example: 2.0.0
 *       500:
 *         description: System unhealthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   enum: [error]
 *                 message:
 *                   type: string
 *                 error:
 *                   type: string
 */
// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW() as time, version() as version');
    res.json({
      status: 'ok',
      timestamp: result.rows[0].time,
      database: 'connected',
      version: '2.0.0'
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Database connection failed',
      error: error.message
    });
  }
});

// Helper function to handle database errors
const handleDbError = (error, res, defaultMessage = 'Database error') => {
  console.error('Database error:', error);
  res.status(500).json({
    error: defaultMessage,
    details: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
};

/**
 * @swagger
 * /api/zones:
 *   get:
 *     tags:
 *       - Zones
 *     summary: Get all zones
 *     description: Retrieve all geographic zones as GeoJSON feature collection
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 type:
 *                   type: string
 *                   enum: [FeatureCollection]
 *                   example: FeatureCollection
 *                 features:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       type:
 *                         type: string
 *                         enum: [Feature]
 *                       geometry:
 *                         type: object
 *                         description: GeoJSON geometry
 *                       properties:
 *                         type: object
 *                         properties:
 *                           id:
 *                             type: string
 *                             format: uuid
 *                           name:
 *                             type: string
 *                           population:
 *                             type: integer
 *       500:
 *         description: Server error
 */
// Get zones as GeoJSON
app.get('/api/zones', async (req, res) => {
  try {
    const query = `
      SELECT
        id,
        name,
        description,
        population,
        area_km2,
        ST_AsGeoJSON(geometry, 6) as geometry
      FROM zones
      ORDER BY name
    `;

    const result = await pool.query(query);

    const features = result.rows.map(row => ({
      type: 'Feature',
      geometry: JSON.parse(row.geometry),
      properties: {
        id: row.id,
        name: row.name,
        description: row.description,
        population: row.population,
        area_km2: row.area_km2
      }
    }));

    const geoJson = {
      type: 'FeatureCollection',
      features
    };

    res.json(geoJson);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch zones');
  }
});

// Get risk assessments for specific time
app.get('/api/risk', async (req, res) => {
  try {
    const { at, timeHorizon } = req.query;

    // Default to current time + 12 hours
    const forecastTime = at ? new Date(at.replace(/-/g, ':')) : new Date(Date.now() + 12 * 60 * 60 * 1000);
    const horizon = timeHorizon || '12h';

    const query = `
      SELECT
        ra.id,
        ra.zone_id,
        ra.time_horizon,
        ra.forecast_time,
        ra.risk_level,
        ra.risk_factors,
        z.name as zone_name,
        z.population,
        z.area_km2
      FROM risk_assessments ra
      JOIN zones z ON ra.zone_id = z.id
      WHERE ra.forecast_time = $1
        AND ra.time_horizon = $2
      ORDER BY ra.risk_level DESC
    `;

    const result = await pool.query(query, [forecastTime, horizon]);

    // Format similar to original JSON structure
    const riskData = result.rows.reduce((acc, row) => {
      acc[row.zone_id] = {
        riskLevel: row.risk_level,
        timeHorizon: row.time_horizon,
        forecastTime: row.forecast_time,
        zoneName: row.zone_name,
        population: row.population,
        areaKm2: row.area_km2,
        riskFactors: row.risk_factors
      };
      return acc;
    }, {});

    res.json(riskData);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch risk data');
  }
});

// Get assets with optional zone filter
app.get('/api/assets', async (req, res) => {
  try {
    const { zoneId } = req.query;

    let query = `
      SELECT
        a.id,
        a.zone_id,
        a.name,
        a.type,
        a.criticality,
        ST_AsGeoJSON(location, 6) as location,
        a.address,
        a.capacity,
        a.metadata,
        z.name as zone_name
      FROM assets a
      JOIN zones z ON a.zone_id = z.id
    `;

    const params = [];
    if (zoneId) {
      query += ' WHERE a.zone_id = $1';
      params.push(zoneId);
    }

    query += ' ORDER BY a.criticality DESC, a.name';

    const result = await pool.query(query, params);

    const assets = result.rows.map(row => ({
      id: row.id,
      zoneId: row.zone_id,
      zoneName: row.zone_name,
      name: row.name,
      type: row.type,
      criticality: row.criticality,
      location: JSON.parse(row.location),
      address: row.address,
      capacity: row.capacity,
      metadata: row.metadata
    }));

    res.json(assets);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch assets');
  }
});

// Get damage index/assessments
app.get('/api/damage-index', async (req, res) => {
  try {
    const { zoneId, assetType } = req.query;

    let query = `
      SELECT
        da.id,
        da.asset_id,
        da.assessment_time,
        da.damage_level,
        da.damage_type,
        da.estimated_cost,
        da.status,
        da.notes,
        a.name as asset_name,
        a.type as asset_type,
        a.zone_id,
        z.name as zone_name
      FROM damage_assessments da
      JOIN assets a ON da.asset_id = a.id
      JOIN zones z ON a.zone_id = z.id
      WHERE da.created_at >= NOW() - INTERVAL '24 hours'
    `;

    const params = [];
    let paramIndex = 1;

    if (zoneId) {
      query += ` AND a.zone_id = $${paramIndex++}`;
      params.push(zoneId);
    }

    if (assetType) {
      query += ` AND a.type = $${paramIndex++}`;
      params.push(assetType);
    }

    query += ' ORDER BY da.assessment_time DESC';

    const result = await pool.query(query, params);

    // Group by zone and calculate overall damage index
    const damageByZone = result.rows.reduce((acc, row) => {
      if (!acc[row.zone_id]) {
        acc[row.zone_id] = {
          zoneName: row.zone_name,
          totalAssets: 0,
          damagedAssets: 0,
          totalDamageLevel: 0,
          estimatedCost: 0,
          assessments: []
        };
      }

      const zone = acc[row.zone_id];
      zone.totalAssets++;
      zone.totalDamageLevel += row.damage_level;
      zone.estimatedCost += parseFloat(row.estimated_cost || 0);

      if (row.damage_level > 0) {
        zone.damagedAssets++;
      }

      zone.assessments.push({
        assetId: row.asset_id,
        assetName: row.asset_name,
        assetType: row.asset_type,
        damageLevel: row.damage_level,
        damageType: row.damage_type,
        estimatedCost: row.estimated_cost,
        status: row.status,
        assessmentTime: row.assessment_time
      });

      return acc;
    }, {});

    // Calculate damage index for each zone (0-100 scale)
    const damageIndex = Object.keys(damageByZone).map(zoneId => {
      const zone = damageByZone[zoneId];
      return {
        zoneId,
        zoneName: zone.zoneName,
        damageIndex: zone.totalAssets > 0 ? Math.round((zone.totalDamageLevel / zone.totalAssets) * 100) : 0,
        totalAssets: zone.totalAssets,
        damagedAssets: zone.damagedAssets,
        estimatedCost: zone.estimatedCost,
        assessments: zone.assessments
      };
    });

    res.json(damageIndex);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch damage index');
  }
});

// Get resources with deployment status
app.get('/api/resources', async (req, res) => {
  try {
    const { status, type } = req.query;

    let query = `
      SELECT
        r.id,
        r.name,
        r.type,
        r.status,
        ST_AsGeoJSON(r.location, 6) as location,
        r.capacity,
        r.capabilities,
        r.contact_info,
        d.zone_id as deployed_zone_id,
        d.deployment_time,
        d.return_time,
        z.name as deployed_zone_name
      FROM resources r
      LEFT JOIN deployments d ON r.id = d.resource_id
        AND d.status IN ('active', 'planned')
      LEFT JOIN zones z ON d.zone_id = z.id
    `;

    const params = [];
    let paramIndex = 1;

    if (status) {
      query += ` WHERE r.status = $${paramIndex++}`;
      params.push(status);
    }

    if (type) {
      query += status ? ` AND r.type = $${paramIndex++}` : ` WHERE r.type = $${paramIndex++}`;
      params.push(type);
    }

    query += ' ORDER BY r.status, r.name';

    const result = await pool.query(query, params);

    const resources = result.rows.map(row => ({
      id: row.id,
      name: row.name,
      type: row.type,
      status: row.status,
      location: row.location ? JSON.parse(row.location) : null,
      capacity: row.capacity,
      capabilities: row.capabilities,
      contactInfo: row.contact_info,
      deployment: row.deployed_zone_id ? {
        zoneId: row.deployed_zone_id,
        zoneName: row.deployed_zone_name,
        deploymentTime: row.deployment_time,
        returnTime: row.return_time
      } : null
    }));

    res.json(resources);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch resources');
  }
});

// Get response plans
app.get('/api/plan', async (req, res) => {
  try {
    const { status, type } = req.query;

    let query = `
      SELECT *
      FROM response_plans
    `;

    const params = [];
    let paramIndex = 1;

    if (status) {
      query += ` WHERE status = $${paramIndex++}`;
      params.push(status);
    }

    if (type) {
      query += status ? ` AND plan_type = $${paramIndex++}` : ` WHERE plan_type = $${paramIndex++}`;
      params.push(type);
    }

    query += ' ORDER BY priority DESC, created_at DESC';

    const result = await pool.query(query, params);

    const plans = result.rows.map(row => ({
      id: row.id,
      name: row.name,
      description: row.description,
      type: row.plan_type,
      triggerConditions: row.trigger_conditions,
      recommendedActions: row.recommended_actions,
      requiredResources: row.required_resources,
      estimatedDuration: row.estimated_duration,
      priority: row.priority,
      status: row.status,
      createdAt: row.created_at,
      updatedAt: row.updated_at
    }));

    res.json(plans);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch response plans');
  }
});

// Get alerts with filtering
app.get('/api/alerts', async (req, res) => {
  try {
    const { severity, acknowledged, zoneId, limit = 50 } = req.query;

    let query = `
      SELECT
        a.*,
        z.name as zone_name
      FROM alerts a
      JOIN zones z ON a.zone_id = z.id
      WHERE a.created_at >= NOW() - INTERVAL '72 hours'
    `;

    const params = [];
    let paramIndex = 1;

    if (severity) {
      query += ` AND a.severity = $${paramIndex++}`;
      params.push(severity);
    }

    if (acknowledged !== undefined) {
      query += ` AND a.acknowledged = $${paramIndex++}`;
      params.push(acknowledged === 'true');
    }

    if (zoneId) {
      query += ` AND a.zone_id = $${paramIndex++}`;
      params.push(zoneId);
    }

    query += ` ORDER BY a.created_at DESC LIMIT $${paramIndex++}`;
    params.push(parseInt(limit));

    const result = await pool.query(query, params);

    const alerts = result.rows.map(row => ({
      id: row.id,
      zoneId: row.zone_id,
      zoneName: row.zone_name,
      severity: row.severity,
      alertType: row.alert_type,
      title: row.title,
      message: row.message,
      acknowledged: row.acknowledged,
      acknowledgedBy: row.acknowledged_by,
      acknowledgedAt: row.acknowledged_at,
      resolved: row.resolved,
      resolvedAt: row.resolved_at,
      metadata: row.metadata,
      createdAt: row.created_at
    }));

    res.json(alerts);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch alerts');
  }
});

// Acknowledge alert
app.post('/api/alerts/:id/ack', async (req, res) => {
  try {
    const { id } = req.params;
    const { acknowledgedBy } = req.body;

    const query = `
      UPDATE alerts
      SET acknowledged = true,
          acknowledged_by = $1,
          acknowledged_at = NOW()
      WHERE id = $2
      RETURNING *
    `;

    const result = await pool.query(query, [acknowledgedBy || 'system', id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Alert not found' });
    }

    res.json({
      success: true,
      message: 'Alert acknowledged successfully',
      alert: result.rows[0]
    });
  } catch (error) {
    handleDbError(error, res, 'Failed to acknowledge alert');
  }
});

// Get communications
app.get('/api/comms', async (req, res) => {
  try {
    const { channel, priority, limit = 100 } = req.query;

    let query = `
      SELECT *
      FROM communications
    `;

    const params = [];
    let paramIndex = 1;

    if (channel) {
      query += ` WHERE channel = $${paramIndex++}`;
      params.push(channel);
    }

    if (priority) {
      query += channel ? ` AND priority = $${paramIndex++}` : ` WHERE priority = $${paramIndex++}`;
      params.push(priority);
    }

    query += ` ORDER BY created_at DESC LIMIT $${paramIndex++}`;
    params.push(parseInt(limit));

    const result = await pool.query(query, params);

    const communications = result.rows.map(row => ({
      id: row.id,
      channel: row.channel,
      sender: row.sender,
      recipient: row.recipient,
      message: row.message,
      direction: row.direction,
      priority: row.priority,
      status: row.status,
      metadata: row.metadata,
      createdAt: row.created_at
    }));

    res.json(communications);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch communications');
  }
});

// Create new communication
app.post('/api/comms', async (req, res) => {
  try {
    const { channel, from, to, message, direction = 'outbound', priority = 'normal' } = req.body;

    const query = `
      INSERT INTO communications (channel, sender, recipient, message, direction, priority)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;

    const result = await pool.query(query, [channel, from, to, message, direction, priority]);

    res.status(201).json({
      success: true,
      communication: result.rows[0]
    });
  } catch (error) {
    handleDbError(error, res, 'Failed to create communication');
  }
});

// Get river gauges
app.get('/api/gauges', async (req, res) => {
  try {
    const { status } = req.query;

    let query = `
      SELECT
        g.*,
        ST_AsGeoJSON(g.location, 6) as location,
        (
          SELECT json_agg(
            json_build_object(
              'readingValue', reading_value,
              'readingTime', reading_time,
              'qualityFlag', quality_flag
            ) ORDER BY reading_time DESC
          )
          FROM (
            SELECT reading_value, reading_time, quality_flag
            FROM gauge_readings
            WHERE gauge_id = g.id
              AND reading_time >= NOW() - INTERVAL '24 hours'
            ORDER BY reading_time DESC
            LIMIT 10
          ) recent_readings
        ) as recentReadings
      FROM gauges g
    `;

    const params = [];
    if (status) {
      query += ' WHERE g.status = $1';
      params.push(status);
    }

    query += ' ORDER BY g.name';

    const result = await pool.query(query, params);

    const gauges = result.rows.map(row => ({
      id: row.id,
      name: row.name,
      location: JSON.parse(row.location),
      riverName: row.river_name,
      gaugeType: row.gauge_type,
      unit: row.unit,
      alertThreshold: row.alert_threshold,
      warningThreshold: row.warning_threshold,
      status: row.status,
      metadata: row.metadata,
      recentReadings: row.recentreadings || []
    }));

    res.json(gauges);
  } catch (error) {
    handleDbError(error, res, 'Failed to fetch gauge data');
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Start server with database connection retry
async function startServer() {
  let retries = 5;
  while (retries > 0) {
    try {
      await pool.query('SELECT NOW()');
      console.log('Database connected successfully');
      break;
    } catch (error) {
      console.error(`Database connection failed (retries left: ${retries - 1}):`, error.message);
      retries--;
      if (retries === 0) {
        console.error('Could not connect to database after multiple retries');
        process.exit(1);
      }
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Flood Prediction API running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`Database: ${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'flood_prediction'}`);
  });
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('Shutting down gracefully...');
  await pool.end();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down gracefully...');
  await pool.end();
  process.exit(0);
});

startServer().catch(console.error);
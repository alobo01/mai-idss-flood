import express from 'express';
import cors from 'cors';
import pkg from 'pg';
import dotenv from 'dotenv';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { fileURLToPath } from 'url';
import swaggerUi from 'swagger-ui-express';
import swaggerJsdoc from 'swagger-jsdoc';

const { Pool } = pkg;

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 18080;

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

// Simple Swagger setup
const swaggerDefinition = {
  openapi: '3.0.3',
  info: {
    title: 'Flood Prediction API',
    version: '2.0.0',
    description: 'PostgreSQL-backed REST API for Flood Prediction System',
    contact: {
      name: 'Flood Prediction System',
      email: 'admin@flood-prediction.local'
    }
  },
  servers: [
    {
      url: 'http://localhost:18080',
      description: 'Development server'
    }
  ]
};

const options = {
  definition: swaggerDefinition,
  apis: [path.join(__dirname, 'server.js')]
};

const specs = swaggerJsdoc(options);

// Swagger UI routes
app.use('/api-docs', swaggerUi.serve);
app.get('/api-docs', swaggerUi.setup(specs, {
  customSiteTitle: 'Flood Prediction API Documentation'
}));

// OpenAPI JSON endpoint
app.get('/api/openapi.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(specs);
});

/**
 * @swagger
 * /health:
 *   get:
 *     tags: [Health]
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
 *                   example: ok
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 database:
 *                   type: string
 *                   example: connected
 *                 version:
 *                   type: string
 *                   example: 2.0.0
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

/**
 * @swagger
 * /api/zones:
 *   get:
 *     tags: [Zones]
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
 *                           name:
 *                             type: string
 *                           population:
 *                             type: integer
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
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch zones',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * @swagger
 * /api/alerts:
 *   get:
 *     tags: [Alerts]
 *     summary: Get alerts
 *     description: Retrieve system alerts with filtering options
 *     parameters:
 *       - in: query
 *         name: severity
 *         schema:
 *           type: string
 *           enum: [low, medium, high, critical]
 *         description: Filter by severity level
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 50
 *         description: Maximum number of alerts to return
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   id:
 *                     type: string
 *                   severity:
 *                     type: string
 *                     enum: [low, medium, high, critical]
 *                   title:
 *                     type: string
 *                   message:
 *                     type: string
 */
// Get alerts with filtering
app.get('/api/alerts', async (req, res) => {
  try {
    const { severity, limit = 50 } = req.query;

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
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch alerts',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * @swagger
 * /api/alerts/{id}/ack:
 *   post:
 *     tags: [Alerts]
 *     summary: Acknowledge alert
 *     description: Mark an alert as acknowledged
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: Alert ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               acknowledgedBy:
 *                 type: string
 *                 description: Name of person acknowledging
 *                 example: John Doe
 *     responses:
 *       200:
 *         description: Alert acknowledged successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 *                 message:
 *                   type: string
 *                   example: Alert acknowledged successfully
 */
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
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to acknowledge alert',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * @swagger
 * /api/resources:
 *   get:
 *     tags: [Resources]
 *     summary: Get resources
 *     description: Retrieve emergency resources with deployment status
 *     parameters:
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *           enum: [available, deployed, standby, maintenance]
 *         description: Filter by resource status
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   id:
 *                     type: string
 *                   name:
 *                     type: string
 *                   type:
 *                     type: string
 *                   status:
 *                     type: string
 *                     enum: [available, deployed, standby, maintenance]
 */
// Get resources with deployment status
app.get('/api/resources', async (req, res) => {
  try {
    const { status } = req.query;

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
    if (status) {
      query += ` WHERE r.status = $1`;
      params.push(status);
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
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch resources',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
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
    console.log(`API Documentation: http://localhost:${PORT}/api-docs`);
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

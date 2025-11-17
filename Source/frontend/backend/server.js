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

const enableSsl = (process.env.DB_SSL || '').toLowerCase() === 'true';

// PostgreSQL connection pool
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'flood_prediction',
  user: process.env.DB_USER || 'flood_user',
  password: process.env.DB_PASSWORD || 'flood_password',
  ssl: enableSsl ? { rejectUnauthorized: false } : false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

const severityDisplayMap = {
  low: 'Low',
  medium: 'Moderate',
  high: 'High',
  critical: 'Severe',
};

const clamp = (value) => Math.min(Math.max(Number(value) || 0, 0), 1);

const determineRiskBand = (value) => {
  if (value >= 0.75) return 'Severe';
  if (value >= 0.5) return 'High';
  if (value >= 0.35) return 'Moderate';
  return 'Low';
};

const parsePoint = (geoJsonText) => {
  if (!geoJsonText) return { lat: null, lng: null };
  try {
    const geometry = JSON.parse(geoJsonText);
    if (geometry?.coordinates) {
      const [lng, lat] = geometry.coordinates;
      return { lat, lng };
    }
  } catch {
    // Ignore parse errors and fall through
  }
  return { lat: null, lng: null };
};

const formatRiskDrivers = (rawFactors) => {
  if (!rawFactors) return [];

  if (Array.isArray(rawFactors)) {
    return rawFactors.map((entry) => ({
      feature: entry.feature || 'factor',
      contribution: clamp(entry.contribution),
    }));
  }

  const entries = Object.entries(rawFactors);
  const sum = entries.reduce((total, [, value]) => total + (Number(value) || 0), 0) || 1;

  return entries.map(([feature, value]) => ({
    feature,
    contribution: Math.round(((Number(value) || 0) / sum) * 100) / 100,
  }));
};

const alertStatus = (row) => {
  if (row.resolved) return 'resolved';
  if (row.acknowledged) return 'acknowledged';
  return 'open';
};

const alertSeverityDisplay = (value) => severityDisplayMap[value] || 'Moderate';

const determineTrend = (current, previous, fallback) => {
  if (current == null || previous == null) {
    return fallback || 'steady';
  }
  const delta = Number(current) - Number(previous);
  if (delta > 0.05) return 'rising';
  if (delta < -0.05) return 'falling';
  return 'steady';
};

const normalizeTimestamp = (value) => {
  if (!value) return null;
  if (value.includes('T') && value.includes('-') && !value.includes(':')) {
    const [datePart, timePartRaw] = value.split('T');
    const hasZone = timePartRaw.endsWith('Z');
    const timeBody = hasZone ? timePartRaw.slice(0, -1) : timePartRaw;
    const normalizedTime = timeBody.replace(/-/g, ':');
    return `${datePart}T${normalizedTime}${hasZone ? 'Z' : ''}`;
  }
  return value;
};

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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
  customSiteTitle: 'Flood Prediction API Documentation',
  customCss: `
    .swagger-ui .topbar { display: none }
    .swagger-ui .info .title { color: #2563eb }
    .swagger-ui .scheme-container { background: #f8fafc; border: 1px solid #e2e8f0; }
    .swagger-ui .opblock.opblock-get { border-color: #22c55e }
    .swagger-ui .opblock.opblock-post { border-color: #3b82f6 }
    .swagger-ui .btn.authorize { background: #2563eb }
  `
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
        code,
        name,
        description,
        population,
        area_km2,
        admin_level,
        critical_assets,
        ST_AsGeoJSON(geometry, 6) as geometry
      FROM zones
      ORDER BY name
    `;

    const result = await pool.query(query);

    const features = result.rows.map(row => ({
      type: 'Feature',
      geometry: JSON.parse(row.geometry),
      properties: {
        id: row.code,
        name: row.name,
        description: row.description,
        population: row.population,
        critical_assets: row.critical_assets || [],
        admin_level: row.admin_level || 10,
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
 * /api/assets:
 *   get:
 *     tags: [Assets]
 *     summary: Get critical assets
 *     description: Retrieve critical infrastructure assets with optional zone filtering
 *     parameters:
 *       - in: query
 *         name: zoneId
 *         schema:
 *           type: string
 *         description: Zone identifier (code like Z-ALFA or UUID)
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
 *                   zoneId:
 *                     type: string
 *                   name:
 *                     type: string
 *                   type:
 *                     type: string
 *                   criticality:
 *                     type: string
 */
app.get('/api/assets', async (req, res) => {
  try {
    const { zoneId } = req.query;
    const params = [];
    const clauses = [];
    let paramIndex = 1;

    if (zoneId) {
      if (uuidPattern.test(zoneId)) {
        clauses.push(`a.zone_id = $${paramIndex++}`);
      } else {
        clauses.push(`z.code = $${paramIndex++}`);
      }
      params.push(zoneId);
    }

    let query = `
      SELECT
        a.id,
        a.name,
        a.type,
        a.criticality,
        ST_AsGeoJSON(a.location, 6) as location,
        a.address,
        a.capacity,
        a.metadata,
        z.id as zone_uuid,
        z.code as zone_code,
        z.name as zone_name
      FROM assets a
      JOIN zones z ON a.zone_id = z.id
    `;

    if (clauses.length > 0) {
      query += ` WHERE ${clauses.join(' AND ')}`;
    }

    query += ' ORDER BY a.criticality DESC, a.name';

    const result = await pool.query(query, params);

    const payload = result.rows.map(row => {
      let location = null;
      if (row.location) {
        try {
          location = JSON.parse(row.location);
        } catch {
          location = null;
        }
      }

      const coords = Array.isArray(location?.coordinates) ? location.coordinates : [null, null];

      return {
        id: row.id,
        zoneId: row.zone_code,
        zoneUuid: row.zone_uuid,
        zoneName: row.zone_name,
        name: row.name,
        type: row.type,
        criticality: row.criticality,
        location,
        lat: coords[1],
        lng: coords[0],
        address: row.address,
        capacity: row.capacity,
        metadata: row.metadata || {},
      };
    });

    res.json(payload);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch assets',
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
        z.name as zone_name,
        z.code as zone_code
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
      id: row.metadata?.externalId || row.id,
      zoneId: row.zone_code,
      severity: alertSeverityDisplay(row.severity),
      type: row.alert_type === 'crew' ? 'Crew' : 'System',
      crewId: row.metadata?.crewId,
      title: row.title,
      description: row.message,
      eta: row.metadata?.eta || null,
      status: row.metadata?.status ?? alertStatus(row),
      timestamp: row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at,
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
      WHERE id::text = $2 OR metadata->>'externalId' = $2
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
 *     description: Retrieve emergency resources with optional filtering by type or status
 *     parameters:
 *       - in: query
 *         name: type
 *         schema:
 *           type: string
 *           enum: [depot, equipment, crew]
 *         description: Filter resources by type
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *           enum: [available, deployed, standby, maintenance, ready, working, rest]
 *         description: Filter resources by current status
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
// Get resources with optional filters
app.get('/api/resources', async (req, res) => {
  try {
    const { type, status } = req.query;

    let query = `
      SELECT
        code,
        name,
        type,
        status,
        capacity,
        capabilities,
        contact_info,
        ST_AsGeoJSON(location, 6) as location
      FROM resources
    `;

    const params = [];
    const clauses = [];
    let paramIndex = 1;

    if (type) {
      clauses.push(`LOWER(type) = LOWER($${paramIndex++})`);
      params.push(type);
    }

    if (status) {
      clauses.push(`LOWER(status) = LOWER($${paramIndex++})`);
      params.push(status);
    }

    if (clauses.length > 0) {
      query += ` WHERE ${clauses.join(' AND ')}`;
    }

    query += ' ORDER BY type, name';

    const result = await pool.query(query, params);

    const payload = {
      depots: [],
      equipment: [],
      crews: []
    };

    result.rows.forEach(row => {
      const location = parsePoint(row.location);
      const capabilities = row.capabilities || {};

      if (row.type === 'depot') {
        payload.depots.push({
          id: row.code,
          name: row.name,
          lat: location.lat,
          lng: location.lng,
        });
        return;
      }

      if (row.type === 'equipment') {
        payload.equipment.push({
          id: row.code,
          type: capabilities.type || row.name,
          subtype: capabilities.subtype,
          capacity_lps: capabilities.capacity_lps,
          units: capabilities.units,
          depot: capabilities.depot,
          status: row.status,
        });
        return;
      }

      if (row.type === 'crew') {
        payload.crews.push({
          id: row.code,
          name: row.name,
          skills: capabilities.skills || [],
          depot: capabilities.depot,
          status: row.status,
          lat: location.lat,
          lng: location.lng,
        });
      }
    });

    res.json(payload);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch resources',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Helper for admin permissions
const getRolePermissions = (role) => {
  const permissions = {
    Administrator: ['system_config', 'user_management', 'threshold_management', 'zone_management', 'risk_assessment', 'resource_deployment'],
    Planner: ['risk_assessment', 'scenario_planning', 'alert_management', 'zone_viewing', 'reporting'],
    Coordinator: ['resource_deployment', 'crew_management', 'communications', 'alert_management', 'zone_viewing'],
    'Data Analyst': ['data_export', 'reporting', 'analytics', 'zone_viewing'],
  };

  return permissions[role] || ['zone_viewing'];
};

const mapAdminUserRow = (row) => ({
  id: row.id,
  username: row.username,
  email: row.email,
  firstName: row.first_name,
  lastName: row.last_name,
  role: row.role,
  department: row.department,
  phone: row.phone,
  location: row.location,
  status: row.status,
  zones: row.zones || [],
  permissions: row.permissions || [],
  createdAt: row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at,
  updatedAt: row.updated_at instanceof Date ? row.updated_at.toISOString() : row.updated_at,
  lastLogin: row.last_login instanceof Date ? row.last_login.toISOString() : row.last_login,
});

const mapRiskThresholdRow = (row) => ({
  id: row.id,
  name: row.name,
  band: row.band,
  minRisk: Number(row.min_risk),
  maxRisk: Number(row.max_risk),
  color: row.color,
  description: row.description,
  autoAlert: row.auto_alert,
});

const mapGaugeThresholdRow = (row) => ({
  id: row.id,
  gaugeCode: row.gauge_code,
  gaugeName: row.gauge_name,
  alertThreshold: row.alert_threshold != null ? Number(row.alert_threshold) : null,
  criticalThreshold: row.critical_threshold != null ? Number(row.critical_threshold) : null,
  unit: row.unit,
  description: row.description,
});

const mapAlertRuleRow = (row) => ({
  id: row.id,
  name: row.name,
  triggerType: row.trigger_type,
  triggerValue: row.trigger_value,
  severity: row.severity,
  enabled: row.enabled,
  channels: row.channels || [],
  cooldownMinutes: row.cooldown_minutes != null ? Number(row.cooldown_minutes) : null,
  description: row.description,
});

const buildAdminResourceExport = (rows) => {
  const exportData = {
    depots: [],
    equipment: [],
    crews: [],
  };

  rows.forEach((row) => {
    const location = parsePoint(row.location);
    const capabilities = row.capabilities || {};
    const contact = row.contact_info || {};

    if (row.type === 'depot') {
      exportData.depots.push({
        id: row.code,
        name: row.name,
        status: row.status,
        lat: location.lat,
        lng: location.lng,
        capacity: row.capacity != null ? Number(row.capacity) : null,
        manager: contact.manager || capabilities.manager || null,
        phone: contact.phone || null,
        address: contact.address || null,
        zones: Array.isArray(capabilities.zones) ? capabilities.zones : [],
      });
      return;
    }

    if (row.type === 'equipment') {
      exportData.equipment.push({
        id: row.code,
        type: capabilities.type || row.name,
        subtype: capabilities.subtype || null,
        capacity: capabilities.capacity_lps || row.capacity,
        units: capabilities.units || null,
        status: row.status,
        depot: capabilities.depot || null,
      });
      return;
    }

    if (row.type === 'crew') {
      exportData.crews.push({
        id: row.code,
        name: row.name,
        status: row.status,
        teamSize: capabilities.team_size || row.capacity,
        skills: capabilities.skills || [],
        depot: capabilities.depot || null,
      });
    }
  });

  return exportData;
};

// Administrative resource endpoints (read-only for dashboard)
app.get('/api/admin/resources/depots', async (req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT
        code,
        name,
        status,
        capacity,
        capabilities,
        contact_info,
        ST_AsGeoJSON(location, 6) AS location
      FROM resources
      WHERE LOWER(type) = 'depot'
      ORDER BY name
    `);

    const depots = rows.map(row => {
      const location = parsePoint(row.location);
      const capabilities = row.capabilities || {};
      const contact = row.contact_info || {};

      return {
        id: row.code || row.id,
        name: row.name,
        lat: location.lat,
        lng: location.lng,
        address: contact.address || null,
        capacity: row.capacity != null ? Number(row.capacity) : null,
        manager: contact.manager || capabilities.manager || null,
        phone: contact.phone || null,
        operatingHours: contact.operating_hours || null,
        status: row.status,
        zones: Array.isArray(capabilities.zones) ? capabilities.zones : [],
      };
    });

    res.json(depots);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to load depots',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

app.get('/api/admin/resources/equipment', async (req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT
        code,
        name,
        status,
        capacity,
        capabilities,
        contact_info
      FROM resources
      WHERE LOWER(type) = 'equipment'
      ORDER BY code
    `);

    const equipment = rows.map(row => {
      const capabilities = row.capabilities || {};
      const contact = row.contact_info || {};

      return {
        id: row.code || row.id,
        type: capabilities.type || row.name,
        subtype: capabilities.subtype || null,
        capacity_lps: capabilities.capacity_lps != null ? Number(capabilities.capacity_lps) : null,
        units: capabilities.units != null ? Number(capabilities.units) : null,
        depot: capabilities.depot || 'Unassigned',
        status: row.status,
        serialNumber: capabilities.serial_number || contact.serial_number || null,
        manufacturer: capabilities.manufacturer || null,
        model: capabilities.model || null,
      };
    });

    res.json(equipment);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to load equipment',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

app.get('/api/admin/resources/crews', async (req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT
        code,
        name,
        status,
        capacity,
        capabilities,
        contact_info,
        ST_AsGeoJSON(location, 6) AS location
      FROM resources
      WHERE LOWER(type) = 'crew'
      ORDER BY name
    `);

    const crews = rows.map(row => {
      const location = parsePoint(row.location);
      const capabilities = row.capabilities || {};
      const contact = row.contact_info || {};

      const teamSize = capabilities.team_size != null
        ? Number(capabilities.team_size)
        : (row.capacity != null ? Number(row.capacity) : null);

      return {
        id: row.code || row.id,
        name: row.name,
        skills: Array.isArray(capabilities.skills) ? capabilities.skills : [],
        depot: capabilities.depot || 'Unassigned',
        status: row.status,
        lat: location.lat,
        lng: location.lng,
        teamSize,
        leader: capabilities.leader || contact.manager || null,
        phone: contact.phone || null,
        certifications: Array.isArray(capabilities.certifications) ? capabilities.certifications : [],
      };
    });

    res.json(crews);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to load crews',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Administrative user management
app.get('/api/admin/users', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM admin_users ORDER BY created_at DESC');
    res.json(rows.map(mapAdminUserRow));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to load users', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.post('/api/admin/users', async (req, res) => {
  const required = ['username', 'email', 'firstName', 'lastName', 'role', 'department', 'status'];
  const missing = required.filter(field => !req.body?.[field]);
  if (missing.length) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  try {
    const { username, email, firstName, lastName, role, department, phone, location, status, zones = [], permissions } = req.body;

    const existing = await pool.query('SELECT 1 FROM admin_users WHERE username = $1 OR email = $2', [username, email]);
    if (existing.rowCount > 0) {
      return res.status(409).json({ error: 'Username or email already exists' });
    }

    const inserted = await pool.query(
      `INSERT INTO admin_users (username, email, first_name, last_name, role, department, phone, location, status, zones, permissions)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
       RETURNING *`,
      [
        username,
        email,
        firstName,
        lastName,
        role,
        department,
        phone || null,
        location || null,
        status || 'active',
        zones,
        permissions && permissions.length ? permissions : getRolePermissions(role),
      ]
    );

    res.status(201).json(mapAdminUserRow(inserted.rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to create user', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.put('/api/admin/users/:id', async (req, res) => {
  try {
    const userId = req.params.id;
    const existing = await pool.query('SELECT * FROM admin_users WHERE id::text = $1', [userId]);
    if (!existing.rows.length) {
      return res.status(404).json({ error: 'User not found' });
    }

    const row = existing.rows[0];
    const nextRole = req.body.role ?? row.role;
    let nextPermissions;
    if (Array.isArray(req.body.permissions)) {
      nextPermissions = req.body.permissions.length ? req.body.permissions : getRolePermissions(nextRole);
    } else if (req.body.role) {
      nextPermissions = getRolePermissions(nextRole);
    } else {
      nextPermissions = row.permissions || getRolePermissions(nextRole);
    }

    const zones = Array.isArray(req.body.zones) ? req.body.zones : (row.zones || []);

    const { rows } = await pool.query(
      `UPDATE admin_users
       SET email = COALESCE($1, email),
           first_name = COALESCE($2, first_name),
           last_name = COALESCE($3, last_name),
           role = COALESCE($4, role),
           department = COALESCE($5, department),
           phone = COALESCE($6, phone),
           location = COALESCE($7, location),
           status = COALESCE($8, status),
           zones = $9,
           permissions = $10,
           updated_at = NOW()
       WHERE id::text = $11
       RETURNING *`,
      [
        req.body.email,
        req.body.firstName,
        req.body.lastName,
        req.body.role,
        req.body.department,
        req.body.phone,
        req.body.location,
        req.body.status,
        zones,
        nextPermissions && nextPermissions.length ? nextPermissions : getRolePermissions(nextRole),
        userId,
      ]
    );

    res.json(mapAdminUserRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to update user', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.delete('/api/admin/users/:id', async (req, res) => {
  try {
    const userId = req.params.id;

    const { rows } = await pool.query('SELECT role FROM admin_users WHERE id::text = $1', [userId]);
    if (!rows.length) {
      return res.status(404).json({ error: 'User not found' });
    }

    if (rows[0].role === 'Administrator') {
      const adminCount = await pool.query(`SELECT COUNT(*)::int AS count FROM admin_users WHERE role = 'Administrator'`);
      if (Number(adminCount.rows[0].count) <= 1) {
        return res.status(400).json({ error: 'Cannot delete the last administrator' });
      }
    }

    await pool.query('DELETE FROM admin_users WHERE id::text = $1', [userId]);
    res.status(204).send();
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to delete user', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

// Risk thresholds
app.get('/api/admin/thresholds/risk', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM admin_risk_thresholds ORDER BY min_risk ASC');
    res.json(rows.map(mapRiskThresholdRow));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to load thresholds', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.post('/api/admin/thresholds/risk', async (req, res) => {
  const { name, band, minRisk, maxRisk, color, description, autoAlert } = req.body || {};
  if (name == null || band == null || minRisk == null || maxRisk == null) {
    return res.status(400).json({ error: 'name, band, minRisk, and maxRisk are required' });
  }
  if (minRisk >= maxRisk || minRisk < 0 || maxRisk > 1) {
    return res.status(400).json({ error: 'Invalid risk values' });
  }
  try {
    const { rows } = await pool.query(
      `INSERT INTO admin_risk_thresholds (name, band, min_risk, max_risk, color, description, auto_alert)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *`,
      [name, band, minRisk, maxRisk, color || null, description || null, autoAlert ?? false]
    );
    res.status(201).json(mapRiskThresholdRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to create threshold', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.put('/api/admin/thresholds/risk/:id', async (req, res) => {
  const { id } = req.params;
  const { name, band, minRisk, maxRisk, color, description, autoAlert } = req.body || {};

  if (minRisk != null && maxRisk != null) {
    if (minRisk >= maxRisk || minRisk < 0 || maxRisk > 1) {
      return res.status(400).json({ error: 'Invalid risk values' });
    }
  }

  try {
    const { rows } = await pool.query(
      `UPDATE admin_risk_thresholds
       SET name = COALESCE($1, name),
           band = COALESCE($2, band),
           min_risk = COALESCE($3, min_risk),
           max_risk = COALESCE($4, max_risk),
           color = COALESCE($5, color),
           description = COALESCE($6, description),
           auto_alert = COALESCE($7, auto_alert),
           updated_at = NOW()
       WHERE id::text = $8 RETURNING *`,
      [name, band, minRisk, maxRisk, color, description, autoAlert, id]
    );

    if (!rows.length) {
      return res.status(404).json({ error: 'Threshold not found' });
    }

    res.json(mapRiskThresholdRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to update threshold', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.delete('/api/admin/thresholds/risk/:id', async (req, res) => {
  try {
    const { rowCount } = await pool.query('DELETE FROM admin_risk_thresholds WHERE id::text = $1', [req.params.id]);
    if (!rowCount) {
      return res.status(404).json({ error: 'Threshold not found' });
    }
    res.status(204).send();
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to delete threshold', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

// Gauge thresholds
app.get('/api/admin/thresholds/gauges', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM admin_gauge_thresholds ORDER BY gauge_name');
    res.json(rows.map(mapGaugeThresholdRow));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to load gauge thresholds', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.post('/api/admin/thresholds/gauges', async (req, res) => {
  const { gaugeCode, gaugeName, alertThreshold, criticalThreshold, unit, description } = req.body || {};
  if (!gaugeCode || !gaugeName) {
    return res.status(400).json({ error: 'gaugeCode and gaugeName are required' });
  }
  try {
    const { rows } = await pool.query(
      `INSERT INTO admin_gauge_thresholds (gauge_code, gauge_name, alert_threshold, critical_threshold, unit, description)
       VALUES ($1,$2,$3,$4,$5,$6) RETURNING *`,
      [gaugeCode, gaugeName, alertThreshold, criticalThreshold, unit || 'meters', description || null]
    );
    res.status(201).json(mapGaugeThresholdRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to create gauge threshold', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.put('/api/admin/thresholds/gauges/:id', async (req, res) => {
  const { id } = req.params;
  const { gaugeCode, gaugeName, alertThreshold, criticalThreshold, unit, description } = req.body || {};
  try {
    const { rows } = await pool.query(
      `UPDATE admin_gauge_thresholds
       SET gauge_code = COALESCE($1, gauge_code),
           gauge_name = COALESCE($2, gauge_name),
           alert_threshold = COALESCE($3, alert_threshold),
           critical_threshold = COALESCE($4, critical_threshold),
           unit = COALESCE($5, unit),
           description = COALESCE($6, description),
           updated_at = NOW()
       WHERE id::text = $7 RETURNING *`,
      [gaugeCode, gaugeName, alertThreshold, criticalThreshold, unit, description, id]
    );

    if (!rows.length) {
      return res.status(404).json({ error: 'Gauge threshold not found' });
    }
    res.json(mapGaugeThresholdRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to update gauge threshold', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.delete('/api/admin/thresholds/gauges/:id', async (req, res) => {
  try {
    const { rowCount } = await pool.query('DELETE FROM admin_gauge_thresholds WHERE id::text = $1', [req.params.id]);
    if (!rowCount) {
      return res.status(404).json({ error: 'Gauge threshold not found' });
    }
    res.status(204).send();
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to delete gauge threshold', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

// Alert rules
app.get('/api/admin/alerts/rules', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM admin_alert_rules ORDER BY created_at DESC');
    res.json(rows.map(mapAlertRuleRow));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to load alert rules', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.post('/api/admin/alerts/rules', async (req, res) => {
  const { name, triggerType, triggerValue, severity, enabled, channels, cooldownMinutes, description } = req.body || {};
  if (!name || !triggerType || !triggerValue || !severity) {
    return res.status(400).json({ error: 'name, triggerType, triggerValue, and severity are required' });
  }
  try {
    const { rows } = await pool.query(
      `INSERT INTO admin_alert_rules (name, trigger_type, trigger_value, severity, enabled, channels, cooldown_minutes, description)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *`,
      [name, triggerType, triggerValue, severity, enabled ?? true, channels && channels.length ? channels : ['Dashboard'], cooldownMinutes ?? 60, description || null]
    );
    res.status(201).json(mapAlertRuleRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to create alert rule', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.put('/api/admin/alerts/rules/:id', async (req, res) => {
  const { id } = req.params;
  const { name, triggerType, triggerValue, severity, enabled, channels, cooldownMinutes, description } = req.body || {};
  try {
    const { rows } = await pool.query(
      `UPDATE admin_alert_rules
       SET name = COALESCE($1, name),
           trigger_type = COALESCE($2, trigger_type),
           trigger_value = COALESCE($3, trigger_value),
           severity = COALESCE($4, severity),
           enabled = COALESCE($5, enabled),
           channels = COALESCE($6, channels),
           cooldown_minutes = COALESCE($7, cooldown_minutes),
           description = COALESCE($8, description),
           updated_at = NOW()
       WHERE id::text = $9 RETURNING *`,
      [name, triggerType, triggerValue, severity, enabled, channels, cooldownMinutes, description, id]
    );

    if (!rows.length) {
      return res.status(404).json({ error: 'Alert rule not found' });
    }
    res.json(mapAlertRuleRow(rows[0]));
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to update alert rule', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.delete('/api/admin/alerts/rules/:id', async (req, res) => {
  try {
    const { rowCount } = await pool.query('DELETE FROM admin_alert_rules WHERE id::text = $1', [req.params.id]);
    if (!rowCount) {
      return res.status(404).json({ error: 'Alert rule not found' });
    }
    res.status(204).send();
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to delete alert rule', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

// Zone management
app.put('/api/admin/zones', async (req, res) => {
  const { geojson } = req.body || {};
  if (!geojson || geojson.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
    return res.status(400).json({ error: 'Invalid GeoJSON payload' });
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    for (const feature of geojson.features) {
      const props = feature.properties || {};
      const code = props.id || props.code;
      if (!code || !feature.geometry) {
        throw new Error('Each feature must include an id/code and geometry');
      }

      const updateResult = await client.query(
        `UPDATE zones
         SET name = COALESCE($2, name),
             description = COALESCE($3, description),
             population = COALESCE($4, population),
             area_km2 = COALESCE($5, area_km2),
             admin_level = COALESCE($6, admin_level),
             critical_assets = COALESCE($7, critical_assets),
             geometry = ST_SetSRID(ST_GeomFromGeoJSON($8), 4326),
             updated_at = NOW()
         WHERE code = $1`,
        [
          code,
          props.name || null,
          props.description || null,
          props.population || null,
          props.area_km2 || null,
          props.admin_level || null,
          props.critical_assets || [],
          JSON.stringify(feature.geometry),
        ]
      );
      if (updateResult.rowCount === 0) {
        throw new Error(`Zone with code ${code} not found`);
      }
    }
    await client.query('COMMIT');

    res.json({ success: true, zones: geojson });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to update zones', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  } finally {
    client.release();
  }
});

// Export helpers
app.get('/api/admin/export/:type', async (req, res) => {
  const { type } = req.params;
  try {
    let data;
    let filename = `${type}.json`;

    switch (type) {
      case 'users': {
        const { rows } = await pool.query('SELECT * FROM admin_users ORDER BY created_at DESC');
        data = rows.map(mapAdminUserRow);
        filename = 'users.json';
        break;
      }
      case 'thresholds': {
        const [risk, gauges, alertsRules] = await Promise.all([
          pool.query('SELECT * FROM admin_risk_thresholds ORDER BY min_risk'),
          pool.query('SELECT * FROM admin_gauge_thresholds ORDER BY gauge_name'),
          pool.query('SELECT * FROM admin_alert_rules ORDER BY name'),
        ]);
        data = {
          risk: risk.rows.map(mapRiskThresholdRow),
          gauges: gauges.rows.map(mapGaugeThresholdRow),
          alerts: alertsRules.rows.map(mapAlertRuleRow),
        };
        filename = 'thresholds.json';
        break;
      }
      case 'resources': {
        const { rows } = await pool.query(`
          SELECT code, name, type, status, capacity, capabilities, contact_info, ST_AsGeoJSON(location, 6) AS location
          FROM resources
          ORDER BY type, name
        `);
        data = buildAdminResourceExport(rows);
        filename = 'resources.json';
        break;
      }
      case 'zones': {
        const { rows } = await pool.query(`
          SELECT code, name, description, population, area_km2, admin_level, critical_assets, ST_AsGeoJSON(geometry, 6) AS geometry
          FROM zones
          ORDER BY name
        `);
        data = {
          type: 'FeatureCollection',
          features: rows.map((row) => ({
            type: 'Feature',
            geometry: JSON.parse(row.geometry),
            properties: {
              id: row.code,
              name: row.name,
              description: row.description,
              population: row.population,
              area_km2: row.area_km2,
              admin_level: row.admin_level,
              critical_assets: row.critical_assets || [],
            },
          })),
        };
        filename = 'zones.geojson';
        break;
      }
      default:
        return res.status(400).json({ error: 'Invalid export type' });
    }

    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.json(data);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to export data', details: process.env.NODE_ENV === 'development' ? error.message : undefined });
  }
});

app.get('/api/risk', async (req, res) => {
  try {
    const { at, timeHorizon } = req.query;
    const horizon = (timeHorizon || '12h').toLowerCase();

    const params = [horizon];
    let filter = 'WHERE ra.time_horizon = $1';

    if (at) {
      const normalized = normalizeTimestamp(at);
      params.push(normalized);
      filter += ` AND ra.forecast_time <= $${params.length}`;
    }

    const query = `
      SELECT
        z.code as zone_code,
        ra.risk_level,
        ra.risk_factors,
        ra.forecast_time
      FROM risk_assessments ra
      JOIN zones z ON ra.zone_id = z.id
      ${filter}
      ORDER BY ra.forecast_time DESC, ra.risk_level DESC
      LIMIT 200
    `;

    const result = await pool.query(query, params);
    const now = new Date();

    const payload = result.rows.map(row => {
      const forecastTime = new Date(row.forecast_time);
      const etaHours = Math.max(0, Math.round((forecastTime - now) / (1000 * 60 * 60)));

      return {
        zoneId: row.zone_code,
        risk: Number(row.risk_level),
        drivers: formatRiskDrivers(row.risk_factors),
        thresholdBand: determineRiskBand(Number(row.risk_level)),
        etaHours,
      };
    });

    res.json(payload);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch risk data',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

app.get('/api/damage-index', async (req, res) => {
  try {
    const { rows: popRows } = await pool.query('SELECT MAX(population)::numeric AS max_pop FROM zones');
    const maxPopulation = Number(popRows[0]?.max_pop) || 1;

    const query = `
      SELECT
        z.code as zone_code,
        z.name,
        z.population,
        COALESCE(AVG(da.damage_level), 0) AS avg_damage,
        COUNT(DISTINCT a.id) AS asset_count,
        COUNT(DISTINCT al.id) AS open_alerts,
        ARRAY_REMOVE(ARRAY_AGG(DISTINCT a.name), NULL) AS impacted_assets
      FROM zones z
      LEFT JOIN assets a ON a.zone_id = z.id
      LEFT JOIN damage_assessments da ON da.asset_id = a.id
      LEFT JOIN alerts al ON al.zone_id = z.id AND al.resolved = false
      GROUP BY z.id
      ORDER BY z.name
    `;

    const result = await pool.query(query);

    const payload = result.rows.map(row => {
      const infraIndex = clamp(Number(row.avg_damage) + 0.05 * Number(row.asset_count));
      const humanBase = Number(row.population) / maxPopulation;
      const humanIndex = clamp(humanBase * 0.6 + (row.open_alerts ? 0.2 : 0));

      const notes = [];
      (row.impacted_assets || []).slice(0, 3).forEach(asset => {
        notes.push(`${asset} requires inspection`);
      });
      if (!notes.length && row.open_alerts > 0) {
        notes.push('Active alerts in region');
      }

      return {
        zoneId: row.zone_code,
        infra_index: Number(infraIndex.toFixed(2)),
        human_index: Number(humanIndex.toFixed(2)),
        notes,
      };
    });

    res.json(payload);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch damage data',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

app.get('/api/gauges', async (req, res) => {
  try {
    const query = `
      WITH latest_readings AS (
        SELECT
          gr.*,
          LAG(gr.reading_value) OVER (PARTITION BY gr.gauge_id ORDER BY gr.reading_time DESC) AS previous_value,
          ROW_NUMBER() OVER (PARTITION BY gr.gauge_id ORDER BY gr.reading_time DESC) AS rn
        FROM gauge_readings gr
      )
      SELECT
        g.code,
        g.name,
        ST_AsGeoJSON(g.location, 6) AS location,
        g.alert_threshold,
        g.warning_threshold,
        g.metadata,
        lr.reading_value,
        lr.previous_value,
        lr.reading_time
      FROM gauges g
      LEFT JOIN latest_readings lr ON lr.gauge_id = g.id AND lr.rn = 1
      ORDER BY g.name
    `;

    const result = await pool.query(query);

    const gauges = result.rows.map(row => {
      const location = parsePoint(row.location);
      const reading = Number(row.reading_value ?? 0);
      const prev = Number(row.previous_value ?? reading);
      const trend = determineTrend(reading, prev, row.metadata?.trend);

      return {
        id: row.code,
        name: row.name,
        lat: location.lat,
        lng: location.lng,
        level_m: reading,
        trend,
        alert_threshold: Number(row.warning_threshold ?? 0),
        critical_threshold: Number(row.alert_threshold ?? 0),
        last_updated: row.reading_time instanceof Date ? row.reading_time.toISOString() : row.reading_time,
      };
    });

    res.json(gauges);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch gauges',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

app.get('/api/comms', async (req, res) => {
  try {
    const { channel, priority, limit = 200 } = req.query;
    let query = `
      SELECT id, channel, sender, recipient, priority, message, created_at, metadata
      FROM communications
    `;

    const params = [];
    const clauses = [];
    let paramIndex = 1;

    if (channel) {
      clauses.push(`channel = $${paramIndex++}`);
      params.push(channel);
    }

    if (priority) {
      clauses.push(`LOWER(priority) = LOWER($${paramIndex++})`);
      params.push(priority);
    }

    if (clauses.length > 0) {
      query += ` WHERE ${clauses.join(' AND ')}`;
    }

    const safeLimit = Math.min(Math.max(parseInt(limit, 10) || 200, 1), 500);
    query += ` ORDER BY created_at DESC LIMIT $${paramIndex++}`;
    params.push(safeLimit);

    const result = await pool.query(query, params);

    const communications = result.rows.map(row => ({
      id: row.metadata?.externalId || row.id,
      channel: row.channel,
      from: row.sender,
      to: row.recipient,
      priority: row.priority,
      text: row.message,
      timestamp: row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at,
    }));

    res.json(communications);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch communications',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

app.post('/api/comms', async (req, res) => {
  try {
    const { channel, from, to, text, priority, direction } = req.body || {};
    if (!channel || !from || !text) {
      return res.status(400).json({ error: 'channel, from, and text are required' });
    }

    const allowedPriorities = ['low', 'normal', 'high', 'urgent'];
    const normalizedPriority = priority?.toString().toLowerCase();
    const finalPriority = allowedPriorities.includes(normalizedPriority) ? normalizedPriority : 'normal';
    const finalDirection = direction === 'inbound' ? 'inbound' : 'outbound';

    const recipient = to || channel;
    const externalId = `COMM-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    const result = await pool.query(
      `
        INSERT INTO communications (channel, sender, recipient, message, direction, priority, status, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, 'sent', $7::jsonb)
        RETURNING created_at, priority, recipient, direction
      `,
      [channel, from, recipient, text, finalDirection, finalPriority, JSON.stringify({ externalId })],
    );

    const createdRow = result.rows[0] || {};
    const createdAt = createdRow.created_at instanceof Date
      ? createdRow.created_at.toISOString()
      : createdRow.created_at;

    res.status(201).json({
      id: externalId,
      channel,
      from,
      to: createdRow.recipient || recipient,
      text,
      priority: createdRow.priority || finalPriority,
      direction: createdRow.direction || finalDirection,
      timestamp: createdAt,
    });
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to record communication',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * @swagger
 * /api/plan:
 *   get:
 *     tags: [Response Plans]
 *     summary: Get the latest response plan
 *     description: Retrieve the latest plan filtered by status (defaults to active) and optional plan type.
 *     parameters:
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *           enum: [draft, active, archived, any]
 *         description: Filter by plan status. Defaults to `active`.
 *       - in: query
 *         name: type
 *         schema:
 *           type: string
 *         description: Filter by plan type (e.g. resource_deployment, evacuation).
 *     responses:
 *       200:
 *         description: Latest plan matching the filters
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 id:
 *                   type: string
 *                 status:
 *                   type: string
 *                 version:
 *                   type: string
 *                 assignments:
 *                   type: array
 *                   items:
 *                     type: object
 *                 coverage:
 *                   type: object
 *       404:
 *         description: No plan available for the given filters
 */
app.get('/api/plan', async (req, res) => {
  try {
    const { status, type } = req.query;
    const filters = [];
    const params = [];
    let paramIndex = 1;

    const statusFilter = (status || 'active').toString().toLowerCase();
    if (statusFilter !== 'any' && statusFilter !== 'all') {
      filters.push(`LOWER(status) = $${paramIndex++}`);
      params.push(statusFilter);
    }

    if (type) {
      filters.push(`LOWER(plan_type) = LOWER($${paramIndex++})`);
      params.push(type);
    }

    let query = `
      SELECT id, name, version, description, plan_type, trigger_conditions,
             recommended_actions, required_resources, assignments, coverage, notes,
             estimated_duration, priority, status, created_at, updated_at
      FROM response_plans
    `;

    if (filters.length > 0) {
      query += ` WHERE ${filters.join(' AND ')}`;
    }

    query += ' ORDER BY created_at DESC LIMIT 1';

    const result = await pool.query(query, params);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'No plan available' });
    }

    const row = result.rows[0];

    res.json({
      id: row.id,
      name: row.name,
      planType: row.plan_type,
      status: row.status,
      version: row.version || (row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at),
      assignments: row.assignments || [],
      coverage: row.coverage || {},
      notes: row.notes || row.description || '',
      triggerConditions: row.trigger_conditions || {},
      recommendedActions: row.recommended_actions || [],
      requiredResources: row.required_resources || {},
      estimatedDuration: row.estimated_duration,
      priority: row.priority,
      createdAt: row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at,
      updatedAt: row.updated_at instanceof Date ? row.updated_at.toISOString() : row.updated_at,
    });
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch plan data',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * @swagger
 * /api/plan/draft:
 *   post:
 *     tags: [Response Plans]
 *     summary: Submit a draft plan
 *     description: Create a new draft response plan with assignments and coverage details.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [assignments]
 *             properties:
 *               name:
 *                 type: string
 *               version:
 *                 type: string
 *                 format: date-time
 *               assignments:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     zoneId:
 *                       type: string
 *                     priority:
 *                       type: integer
 *                     actions:
 *                       type: array
 *                       items:
 *                         type: object
 *               coverage:
 *                 type: object
 *               notes:
 *                 type: string
 *     responses:
 *       201:
 *         description: Draft plan created
 *       400:
 *         description: Invalid payload
 */
app.post('/api/plan/draft', async (req, res) => {
  try {
    const body = req.body || {};
    const assignmentsInput = body.assignments;

    if (!Array.isArray(assignmentsInput) || assignmentsInput.length === 0) {
      return res.status(400).json({ error: 'assignments must be a non-empty array' });
    }

    const sanitizedAssignments = [];
    for (let index = 0; index < assignmentsInput.length; index += 1) {
      const assignment = assignmentsInput[index];
      if (!assignment || typeof assignment.zoneId !== 'string' || !assignment.zoneId.trim()) {
        return res.status(400).json({ error: `assignments[${index}].zoneId is required` });
      }
      if (!Array.isArray(assignment.actions) || assignment.actions.length === 0) {
        return res.status(400).json({ error: `assignments[${index}].actions must contain at least one action` });
      }

      sanitizedAssignments.push({
        zoneId: assignment.zoneId,
        priority: Number.isFinite(Number(assignment.priority))
          ? Number(assignment.priority)
          : index + 1,
        actions: assignment.actions,
        notes: assignment.notes || null,
      });
    }

    const defaultName = `Planner Draft ${uuidv4().slice(0, 8).toUpperCase()}`;
    const planName = body.name?.trim() || defaultName;
    const planVersion = body.version || new Date().toISOString();
    const planType = body.planType || 'resource_deployment';
    const triggerConditions = body.triggerConditions && typeof body.triggerConditions === 'object'
      ? body.triggerConditions
      : {};
    const recommendedActions = Array.isArray(body.recommendedActions) ? body.recommendedActions : [];
    const requiredResources = body.requiredResources && typeof body.requiredResources === 'object'
      ? body.requiredResources
      : {};
    const coverage = body.coverage && typeof body.coverage === 'object' ? body.coverage : {};
    const notes = typeof body.notes === 'string' ? body.notes : '';
    const description = typeof body.description === 'string' && body.description.length > 0
      ? body.description
      : 'Planner submitted draft plan';
    const estimatedDuration = Number.isFinite(Number(body.estimatedDuration))
      ? Math.round(Number(body.estimatedDuration))
      : null;

    const allowedPlanPriorities = ['low', 'medium', 'high', 'critical'];
    const normalizedPlanPriority = body.priority?.toString().toLowerCase();
    const planPriority = allowedPlanPriorities.includes(normalizedPlanPriority)
      ? normalizedPlanPriority
      : 'medium';

    const insertQuery = `
      INSERT INTO response_plans
        (name, version, description, plan_type, trigger_conditions, recommended_actions,
         required_resources, assignments, coverage, notes, estimated_duration, priority, status)
      VALUES
        ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb, $10, $11, $12, 'draft')
      RETURNING id, name, version, plan_type, trigger_conditions, recommended_actions,
        required_resources, assignments, coverage, notes, estimated_duration, priority,
        status, created_at, updated_at
    `;

    const params = [
      planName,
      planVersion,
      description,
      planType,
      JSON.stringify(triggerConditions),
      JSON.stringify(recommendedActions),
      JSON.stringify(requiredResources),
      JSON.stringify(sanitizedAssignments),
      JSON.stringify(coverage),
      notes,
      estimatedDuration,
      planPriority,
    ];

    const result = await pool.query(insertQuery, params);
    const row = result.rows[0];

    res.status(201).json({
      id: row.id,
      name: row.name,
      planType: row.plan_type,
      status: row.status,
      version: row.version,
      assignments: row.assignments,
      coverage: row.coverage,
      notes: row.notes,
      triggerConditions: row.trigger_conditions,
      recommendedActions: row.recommended_actions,
      requiredResources: row.required_resources,
      estimatedDuration: row.estimated_duration,
      priority: row.priority,
      createdAt: row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at,
      updatedAt: row.updated_at instanceof Date ? row.updated_at.toISOString() : row.updated_at,
    });
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to create draft plan',
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

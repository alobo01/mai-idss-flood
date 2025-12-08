import express from 'express';
import cors from 'cors';
import pkg from 'pg';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import swaggerUi from 'swagger-ui-express';
import { specs } from './config/swagger.js';

import healthRoutes from './routes/health.js';
import zonesRoutes from './routes/zones.js';
import alertsRoutes from './routes/alerts.js';
import resourcesRoutes from './routes/resources.js';

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

// Middleware
app.use(cors());
app.use(express.json());

// Make pool available to routes
app.use((req, res, next) => {
  req.pool = pool;
  next();
});

// Simple Swagger setup
const swaggerOptions = {
  customCss: `
    .swagger-ui .topbar { display: none }
    .swagger-ui .info { margin: 20px 0 }
    .swagger-ui .scheme-container { margin: 20px 0 }
  `,
  customSiteTitle: 'Flood Prediction API Documentation'
};

// Swagger UI routes
app.use('/api-docs', swaggerUi.serve);
app.get('/api-docs', swaggerUi.setup(specs, swaggerOptions));

// OpenAPI JSON endpoint
app.get('/api/openapi.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(specs);
});

// API Routes
app.use('/health', healthRoutes);
app.use('/api/zones', zonesRoutes);
app.use('/api/alerts', alertsRoutes);
app.use('/api/resources', resourcesRoutes);

// Serve static files from frontend build
app.use(express.static(path.join(__dirname, '../dist')));

// Catch-all handler: serve index.html for any request that doesn't match API routes
app.get('*', (req, res) => {
  if (req.path.startsWith('/api') || req.path.startsWith('/health')) {
    return res.status(404).json({
      error: 'Endpoint not found',
      path: req.path
    });
  }

  res.sendFile(path.join(__dirname, '../dist/index.html'));
});

// Global error handler
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);

  res.status(error.status || 500).json({
    error: 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Flood Prediction API Server running on port ${PORT}`);
  console.log(`📚 API Documentation: http://localhost:${PORT}/api-docs`);
  console.log(`🏥 Health Check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🔄 Shutting down gracefully...');

  try {
    await pool.end();
    console.log('✅ Database connection closed');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error during shutdown:', error);
    process.exit(1);
  }
});

process.on('SIGTERM', async () => {
  console.log('\n🔄 SIGTERM received, shutting down gracefully...');

  try {
    await pool.end();
    console.log('✅ Database connection closed');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error during shutdown:', error);
    process.exit(1);
  }
});

export default app;
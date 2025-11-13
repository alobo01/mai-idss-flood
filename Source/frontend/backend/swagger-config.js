import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

const options = {
  definition: {
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
        url: 'http://localhost:8080',
        description: 'Development server'
      }
    ],
    tags: [
      { name: 'Health', description: 'System health and status endpoints' },
      { name: 'Zones', description: 'Geographic zone management and visualization' },
      { name: 'Risk', description: 'Risk assessment and prediction data' },
      { name: 'Assets', description: 'Critical infrastructure and assets' },
      { name: 'Resources', description: 'Emergency resources and deployment' },
      { name: 'Alerts', description: 'System alerts and notifications' },
      { name: 'Communications', description: 'Communication logs and messaging' },
      { name: 'Gauges', description: 'River gauge monitoring data' }
    ]
  },
  apis: ['./server.js']
};

export const specs = swaggerJsdoc(options);

export const swaggerUiOptions = {
  explorer: true,
  swaggerOptions: {
    persistAuthorization: true,
    displayRequestDuration: true,
    filter: true,
    showExtensions: true,
    showCommonExtensions: true,
    docExpansion: 'list',
    defaultModelsExpandDepth: 2,
    defaultModelExpandDepth: 2,
  },
  customSiteTitle: 'Flood Prediction API Documentation',
  customCss: `
    .swagger-ui .topbar { display: none }
    .swagger-ui .info .title { color: #2563eb }
    .swagger-ui .scheme-container { background: #f8fafc; border: 1px solid #e2e8f0; }
    .swagger-ui .opblock.opblock-get { border-color: #22c55e }
    .swagger-ui .opblock.opblock-post { border-color: #3b82f6 }
    .swagger-ui .btn.authorize { background: #2563eb }
  `
};

export { swaggerUi };
import swaggerJsdoc from 'swagger-jsdoc';

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Flood Prediction API',
      version: '1.0.0',
      description: 'RESTful API for flood prediction system management including risk assessment, resource allocation, and alert management',
      contact: {
        name: 'API Support',
        email: 'support@floodprediction.com'
      }
    },
    servers: [
      {
        url: process.env.API_BASE_URL || 'http://localhost:18080',
        description: 'Development server'
      }
    ],
    components: {
      schemas: {
        Zone: {
          type: 'object',
          properties: {
            id: { type: 'string', description: 'Unique zone identifier' },
            name: { type: 'string', description: 'Zone name' },
            population: { type: 'number', description: 'Population count' },
            critical_assets: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of critical infrastructure assets'
            },
            admin_level: { type: 'number', description: 'Administrative level (1-15)' }
          }
        },
        Alert: {
          type: 'object',
          properties: {
            id: { type: 'string', description: 'Alert ID' },
            zoneId: { type: 'string', description: 'Zone identifier' },
            severity: {
              type: 'string',
              enum: ['Low', 'Moderate', 'High', 'Severe'],
              description: 'Alert severity level'
            },
            type: { type: 'string', description: 'Alert type' },
            title: { type: 'string', description: 'Alert title' },
            description: { type: 'string', description: 'Alert description' },
            status: {
              type: 'string',
              enum: ['open', 'acknowledged', 'resolved'],
              description: 'Alert status'
            },
            timestamp: {
              type: 'string',
              format: 'date-time',
              description: 'Alert creation timestamp'
            }
          }
        },
        Resource: {
          type: 'object',
          properties: {
            id: { type: 'string', description: 'Resource ID' },
            name: { type: 'string', description: 'Resource name' },
            type: {
              type: 'string',
              enum: ['depot', 'equipment', 'crew'],
              description: 'Resource type'
            },
            status: { type: 'string', description: 'Current status' },
            location: {
              type: 'object',
              properties: {
                lat: { type: 'number', description: 'Latitude' },
                lng: { type: 'number', description: 'Longitude' }
              }
            }
          }
        },
        Error: {
          type: 'object',
          properties: {
            error: { type: 'string', description: 'Error message' },
            details: { type: 'string', description: 'Detailed error information' }
          }
        }
      }
    },
    tags: [
      {
        name: 'Health',
        description: 'Health check endpoints'
      },
      {
        name: 'Zones',
        description: 'Zone management endpoints'
      },
      {
        name: 'Alerts',
        description: 'Alert management endpoints'
      },
      {
        name: 'Resources',
        description: 'Resource management endpoints'
      }
    ]
  },
  apis: ['./routes/*.js'], // Path to route files containing OpenAPI definitions
};

export const specs = swaggerJsdoc(options);
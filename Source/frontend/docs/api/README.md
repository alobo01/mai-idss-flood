# Flood Prediction API Documentation

Complete documentation for the Flood Prediction System REST API with PostgreSQL backend and PostGIS geospatial capabilities.

## 🚀 Quick Start

### Access the API

- **Base URL**: `http://localhost:18080`
- **Interactive Documentation**: `http://localhost:18080/api-docs/`
- **Health Check**: `http://localhost:18080/health`
- **OpenAPI Spec**: `http://localhost:18080/api/openapi.json`

### Try It Now

1. **Open** `http://localhost:18080/api-docs/` in your browser
2. **Click** on any endpoint to expand it
3. **Click** "Try it out" button
4. **Execute** to see real database responses
5. **Seed sample data** with `cd backend && npm run db:seed` (uses `public/mock` or `MOCK_DATA_PATH`)

## 📊 API Overview

### Architecture

The Flood Prediction API is built on:
- **Node.js + Express.js**: RESTful API server
- **PostgreSQL + PostGIS**: Geospatial database for flood prediction data
- **Swagger/OpenAPI 3.0**: Interactive API documentation
- **Docker**: Containerized deployment
- **Connection Pooling**: Efficient database connection management

### Key Features

- **🗺️ Geospatial Data**: Real flood zones with PostGIS polygon support
- **⚡ Real-time Data**: Live alerts, risk assessments, and resource tracking
- **🔍 Advanced Filtering**: Zone-based, time-based, and severity-based filtering
- **📊 Risk Analytics**: Multi-horizon flood risk predictions (6h-72h)
- **🚨 Alert Management**: Alert acknowledgment and resolution tracking
- **📡 Communications**: Multi-channel communication logging and management
- **🛠️ Resource Management**: Emergency crew and equipment deployment tracking
- **🌡️ Environmental Monitoring**: River gauge data and threshold alerts

### Data Models

The API manages comprehensive flood prediction data including:

- **Zones**: Geographic areas with population and critical infrastructure
- **Risk Assessments**: Time-based flood risk predictions with multiple horizons
- **Assets**: Critical infrastructure (hospitals, schools, power plants, etc.)
- **Alerts**: System notifications with severity levels and acknowledgment status
- **Resources**: Emergency teams and equipment with deployment tracking
- **Communications**: Multi-channel messaging logs and management
- **Gauges**: River monitoring stations with real-time readings
- **Damage Assessments**: Infrastructure damage evaluation and cost estimates
- **Response Plans**: Emergency procedures and resource allocation templates

## 🗂️ Database Schema

### Core Tables

1. **zones** - Geographic flood zones
2. **risk_assessments** - Time-based risk predictions
3. **assets** - Critical infrastructure
4. **damage_assessments** - Damage evaluation records
5. **resources** - Emergency teams and equipment
6. **deployments** - Resource deployment tracking
7. **alerts** - System notifications
8. **communications** - Message logs
9. **gauges** - River monitoring stations
10. **gauge_readings** - Historical gauge data
11. **response_plans** - Emergency procedures

### Geospatial Features

- **PostGIS Extension**: Full spatial database capabilities
- **Polygon Geometries**: Zone boundaries for geographic analysis
- **Point Geometries**: Asset locations and gauge positions
- **Spatial Queries**: Distance calculations and containment analysis
- **GeoJSON Export**: Direct support for mapping applications

## 📡 Available Endpoints

### Health & System
- `GET /health` - System health and database connectivity
- `GET /api-docs` - Interactive API documentation
- `GET /api/openapi.json` - OpenAPI specification

### Geographic Data
- `GET /api/zones` - All flood zones as GeoJSON
- `GET /api/assets` - Critical infrastructure with zone mapping

### Risk & Assessment
- `GET /api/risk` - Risk assessments with Postgres-backed horizons and drivers
- `GET /api/damage-index` - Damage index per zone (aggregated from assessments + alerts)

### Operations & Management
- `GET /api/alerts` - System alerts with filtering and ACK state
- `POST /api/alerts/{id}/ack` - Alert acknowledgment
- `GET /api/resources` - Depots, equipment, and crews
- `GET /api/comms` - Communication logs
- `POST /api/comms` - Send communications (persists)

### Monitoring & Analytics
- `GET /api/gauges` - River gauge monitoring data with trend detection
- `GET /api/plan` - Latest response plan (JSON assignments + coverage)

## 🔧 Authentication & Security

### Current Status
- **Development Mode**: No authentication required
- **CORS Enabled**: Cross-origin requests supported
- **Input Validation**: Comprehensive parameter validation
- **Error Handling**: Detailed error responses with logging

### Future Security Features
- API key authentication (ready for implementation)
- Role-based access control
- Request rate limiting
- Audit logging

## 📊 Response Formats

### Success Responses
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150
  }
}
```

### Error Responses
```json
{
  "error": "Description of error",
  "details": "Detailed error information (development only)",
  "code": "ERROR_CODE"
}
```

### Geospatial Responses
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [...]
      },
      "properties": {
        "id": "zone-uuid",
        "name": "Zone Name",
        "population": 15000
      }
    }
  ]
}
```

## 🧪 Testing

### Using Swagger UI
The interactive Swagger UI at `http://localhost:18080/api-docs/` provides:
- **Try It Now** functionality for all endpoints
- **Parameter validation** with examples
- **Response examples** with actual database data
- **Request/Response schemas** for data modeling

### curl Examples
```bash
# Health check
curl http://localhost:18080/health

# Get all zones
curl http://localhost:18080/api/zones

# Get recent alerts
curl http://localhost:18080/api/alerts?limit=10

# Get resources by status
curl http://localhost:18080/api/resources?status=available
```

### Testing Tools
- **Postman**: Import OpenAPI spec from `/api/openapi.json`
- **Swagger UI**: Interactive testing in browser
- **curl**: Command-line testing
- **JavaScript/TypeScript**: Client application development

## 🔧 Configuration

### Environment Variables
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flood_prediction
DB_USER=flood_user
DB_PASSWORD=flood_password
NODE_ENV=development
PORT=18080
```

### Database Connection
- **Connection Pool**: 20 maximum connections
- **Retry Logic**: 5 attempts with 5-second delays
- **Health Checks**: Continuous connection validation
- **Timeout Settings**: 2-second connection timeout

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run all services
docker compose up --build

# Check service status
docker compose ps

# View logs
docker compose logs backend
```

### Service Dependencies
- **PostgreSQL**: Database with PostGIS extensions
- **Backend**: API server with health checks
- **Frontend**: Web interface with nginx proxy

### Health Monitoring
- Database connectivity checks
- Automatic service restarts
- Container health checks
- Graceful shutdown handling

## 📚 Additional Documentation

- **[API Reference](reference.md)** - Detailed endpoint documentation
- **[Database Schema](database.md)** - Complete database structure
- **[API Testing](testing.md)** - Testing strategies and examples
- **[Deployment Guide](../deployment.md)** - Production deployment instructions

## 🆘 Support

For API issues or questions:
1. Check the interactive documentation at `/api-docs`
2. Verify database connectivity with `/health`
3. Review application logs for error details
4. Test with the provided curl examples
5. Check Docker container status with `docker compose ps`

---

**Built with ❤️ for flood prediction and emergency management**

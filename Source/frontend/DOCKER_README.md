# Docker Compose Setup

This document explains the Docker Compose setup for the Flood Prediction System, which now exposes a single PostgreSQL-backed API.

## Services

### 1. PostgreSQL Database
- **Container**: `flood-postgres`
- **Port**: `5433` (host) → `5432` (container)
- **Image**: `postgis/postgis:15-3.3`
- **Purpose**: Spatial database for geographic flood data
- **Health Check**: Ensures PostgreSQL is ready to accept connections

### 2. Backend API (PostgreSQL)
- **Container**: `flood-backend`
- **Port**: `18080`
- **Purpose**: Production backend with database connectivity
- **Health Check**: Verifies API endpoints are responding
- **Environment**: Production mode with database configuration

### 3. Frontend Web Application
- **Container**: `flood-frontend`
- **Port**: `80` (nginx serving built React app)
- **Purpose**: Production frontend application
- **Dependencies**: Waits for the backend API to be healthy
- **Environment**:
  - `VITE_API_BASE_URL=http://backend:18080`
  - `VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`

## Architecture

```
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│   Frontend      │  HTTP  │   Backend API   │  SQL   │   PostgreSQL    │
│   (Port 80)     │◄──────►│   (Port 18080)  │◄──────►│   (Port 5433)   │
│   React + nginx │        │   Express/PG    │        │   PostGIS       │
└─────────────────┘        └─────────────────┘        └─────────────────┘
```

## New Features

### Role Switching for Administrators
Administrators can now switch between different role views:
- **Administrator**: Full admin access with user/resource management
- **Planner**: Risk assessment and scenario planning
- **Coordinator**: Live operations and resource deployment
- **Data Analyst**: Analytics and reporting

### Admin Endpoints
The API provides comprehensive admin functionality:
- **User Management**: Create, update, delete users
- **Resource Management**: Manage depots, equipment, and crews
- **Zone Management**: Edit geographic zones
- **Threshold Configuration**: Set risk and alert thresholds

## Usage

### Development (Local)
```bash
# Start all services
docker compose up --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Production
```bash
# Production deployment
docker compose -f docker-compose.yml up -d --build
```

### Accessing Services
- **Frontend**: http://localhost
- **API**: http://localhost:18080
- **Database**: localhost:5433

### API Endpoints
```bash
# Health check
curl http://localhost:18080/health

# Zones data
curl http://localhost:18080/api/zones

# Admin resources
curl http://localhost:18080/api/admin/resources/depots
curl http://localhost:18080/api/admin/resources/equipment
curl http://localhost:18080/api/admin/resources/crews
```

## Environment Variables

### Frontend
- `VITE_API_BASE_URL`: API base URL (backend:18080)
- `VITE_MAP_TILES_URL`: Map tile server URL
- `NODE_ENV`: Environment mode (production)

### Backend
- `PORT`: Server port (18080)
- `DB_HOST`: Database hostname (postgres)
- `DB_PORT`: Database port (5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

## Health Checks

All services include health checks:
- **PostgreSQL**: Database connectivity
- **Backend**: HTTP health endpoint
- **Frontend**: Waits for backend health check to pass

## Data Persistence

- **PostgreSQL**: Volume `postgres_data` for database persistence
- **Frontend/backend**: Stateless containers rebuilt from source

## Security

- **CORS**: API allows cross-origin requests
- **Network**: All services communicate within Docker network `flood-network`
- **Ports**: Only necessary ports exposed to host

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check if ports 80, 18080, 5433 are available
2. **Health check failures**: Verify service dependencies and logs
3. **Build failures**: Check Dockerfile and package.json files

### Debug Commands
```bash
# Check service status
docker compose ps

# View service logs
docker compose logs backend
docker compose logs web

# Execute shell in container
docker compose exec web sh

# Rebuild specific service
docker compose up --build backend
```

## Development Workflow

1. **Local Development**: Use `npm run dev:full` for hot reloading
2. **Docker Development**: Use `docker compose up --build` for containerized development
3. **Production**: Use `docker compose -f docker-compose.yml up -d --build`

## Next Steps

- Set up CI/CD pipeline for automated builds
- Configure monitoring and logging
- Set up backup strategies for database
- Implement SSL/TLS for production deployment

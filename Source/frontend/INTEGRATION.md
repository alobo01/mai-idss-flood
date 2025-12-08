# Frontend-Backend Integration Guide

## Overview

This document describes the complete integration between the React frontend and the Python FastAPI backend, ensuring all functionality from the original Node.js backend is available and properly configured.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx Proxy    │    │  Python Backend │
│   (React/Vite)  │◄──►│   (Port 80)      │◄──►│   (Port 18080)   │
│                 │    │                 │    │                 │
│ - UI Components │    │ - Static Files  │    │ - FastAPI API   │
│ - State Mgmt    │    │ - API Proxy     │    │ - PostgreSQL    │
│ - Maps          │    │ - CORS Headers  │    │ - Pydantic       │
│ - Charts        │    │ - Load Balance  │    │ - Async/Await   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Configuration

### Environment Variables

The frontend uses the following environment variables:

```bash
# Development (.env.development)
VITE_API_BASE_URL=http://localhost:18080/api
VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png

# Production (.env.production)
VITE_API_BASE_URL=/api
VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

### Docker Configuration

The `docker-compose.yml` is already configured to:

1. **Build and run the Python backend** from `python_backend/Dockerfile`
2. **Build and serve the React frontend** from the current directory
3. **Run PostgreSQL with PostGIS** for spatial data
4. **Configure nginx** as a reverse proxy
5. **Handle health checks** and service dependencies

### Nginx Configuration

The nginx configuration (`nginx.conf`) provides:

- **Static file serving** for the React app
- **API proxy** from `/api/*` to `backend:18080/api/*`
- **CORS headers** for frontend-backend communication
- **API documentation** proxy at `/api-docs`
- **Health check** endpoint at `/health`

## API Endpoints

### Core Endpoints (✅ Fully Compatible)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/health` | GET | Health check | ✅ Working |
| `/api/zones` | GET | Zone data as GeoJSON | ✅ Working |
| `/api/alerts` | GET | Alert management | ✅ Working |
| `/api/alerts/{id}/ack` | POST | Acknowledge alert | ✅ Working |
| `/api/resources` | GET | Resource data | ✅ Working |
| `/api/assets` | GET | Critical assets | ✅ Working |
| `/api/risk` | GET | Risk assessment | ✅ Working |
| `/api/gauges` | GET | River gauge data | ✅ Working |
| `/api/comms` | GET | Communications | ✅ Working |
| `/api/comms` | POST | Send communication | ✅ Working |
| `/api/plan` | GET | Response plans | ✅ Working |
| `/api/plan/draft` | POST | Create draft plan | ✅ Working |
| `/api/damage-index` | GET | Damage assessment | ✅ Working |

### New Prediction Endpoints (🆕 Added)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/predict/river-level` | GET | River level predictions | ✅ Working |
| `/api/predict/flood-risk` | POST | Flood risk predictions | ✅ Working |
| `/api/rule-based/zones` | GET | Rule-based zone analysis | ✅ Working |
| `/api/rule-based/allocate` | POST | Resource allocation | ✅ Working |

### Admin Endpoints (✅ Fully Compatible)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/admin/users` | GET | User management | ✅ Working |
| `/api/admin/users` | POST | Create user | ✅ Working |
| `/api/admin/users/{id}` | PUT | Update user | ✅ Working |
| `/api/admin/users/{id}` | DELETE | Delete user | ✅ Working |
| `/api/admin/resources/*` | GET | Resource admin data | ✅ Working |
| `/api/admin/thresholds/*` | CRUD | Threshold management | ✅ Working |
| `/api/admin/alerts/rules` | CRUD | Alert rule management | ✅ Working |
| `/api/admin/export/{type}` | GET | Data export | ✅ Working |

## Frontend API Integration

### React Query Hooks

The frontend uses React Query for data fetching with these hooks:

```typescript
// Core data hooks (src/hooks/useApiData.ts)
useZones()
useAlerts()
useResources()
useRiskData()
useGauges()
useCommunications()
useDamageIndex()
usePlan()

// New prediction hooks (src/hooks/usePredictions.ts)
useRiverLevelPredictions(gaugeCode, horizon)
useFloodRiskPrediction(request)

// New rule-based hooks (src/hooks/useRuleBased.ts)
useRuleBasedZones(filters)
useRuleBasedAllocation()
```

### API Base Configuration

```typescript
// src/lib/apiBase.ts
export const getApiBaseUrl = (): string => {
  const base = rawBaseUrl().replace(/\/+$/, '');
  if (base.startsWith('http://') || base.startsWith('https://')) {
    return base;
  }
  return base.toLowerCase().endsWith('/api') ? base : `${base}/api`;
};

export const buildApiUrl = (endpoint: string): string => {
  const base = getApiBaseUrl();
  const normalized = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${base}${normalized}`;
};
```

## Data Format Compatibility

### Zone Data (GeoJSON)
```typescript
// Frontend expects:
interface ZoneProperties {
  id: string;
  name: string;
  population: number;
  critical_assets: string[];
  admin_level: number;
}

// Python backend returns exactly this format ✅
```

### Alert Data
```typescript
// Frontend expects:
interface Alert {
  id: string;
  zoneId: string;
  severity: AlertSeverity;
  type: AlertType;
  title: string;
  description: string;
  status: AlertStatus;
  timestamp: string;
}

// Python backend AlertResponse matches exactly ✅
```

### Resource Data
```typescript
// Frontend expects:
interface Resources {
  depots: Depot[];
  equipment: Equipment[];
  crews: Crew[];
}

// Python backend ResourcesResponse matches exactly ✅
```

## Running the Application

### Development Setup

1. **Start with Docker (Recommended):**
   ```bash
   docker compose up --build
   ```

2. **Access the Application:**
   - Frontend: http://localhost
   - API Documentation: http://localhost/api-docs
   - Health Check: http://localhost/health

3. **Manual Testing:**
   ```bash
   # Run the integration verification script
   ./verify-integration.sh
   ```

### Local Development

1. **Backend only:**
   ```bash
   cd python_backend
   python3 -m uvicorn app.main:app --reload --port 18080
   ```

2. **Frontend only:**
   ```bash
   npm run dev
   # Configure VITE_API_BASE_URL=http://localhost:18080/api
   ```

### Testing

```bash
# Run API integration tests
npx playwright test tests/api.spec.ts

# Run full E2E tests
npx playwright test

# Run integration verification
./verify-integration.sh
```

## Migration Notes

### From Node.js to Python Backend

1. **All endpoints are now available** in Python ✅
2. **Response formats are identical** ✅
3. **Error handling is improved** with FastAPI ✅
4. **Type safety is enhanced** with Pydantic schemas ✅
5. **Performance is better** with async/await ✅

### Breaking Changes

None! The migration is fully backward compatible. The frontend will work seamlessly with the Python backend.

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure nginx proxy is configured correctly
   - Check that `VITE_API_BASE_URL` is set properly

2. **API Connection Refused**
   - Verify Python backend is running on port 18080
   - Check Docker health checks: `docker compose ps`

3. **Missing Data**
   - Ensure PostgreSQL is initialized with seed data
   - Check database connection: `curl http://localhost:18080/health`

4. **Build Errors**
   - Clear Docker cache: `docker system prune -a`
   - Rebuild: `docker compose up --build --force-recreate`

### Debug Commands

```bash
# Check backend health
curl http://localhost:18080/health

# Check API docs
curl http://localhost:18080/api-docs

# Test specific endpoint
curl http://localhost:18080/api/zones | jq .

# Check Docker logs
docker compose logs backend
docker compose logs web
```

## Performance Considerations

### Caching
- **React Query** handles client-side caching with configurable stale times
- **Nginx** serves static assets with long cache headers
- **API responses** include appropriate cache headers

### Optimization
- **Async database operations** for better performance
- **Connection pooling** configured for PostgreSQL
- **Gzip compression** enabled in nginx
- **Code splitting** in React build

## Security Features

- **CORS configuration** in nginx
- **Input validation** with Pydantic schemas
- **SQL injection prevention** with SQLAlchemy
- **Rate limiting** can be added to FastAPI
- **Authentication** ready for implementation

## Future Enhancements

1. **WebSocket support** for real-time updates
2. **Authentication/Authorization** system
3. **Advanced caching** with Redis
4. **API versioning** for backward compatibility
5. **Monitoring and logging** integration
6. **Load balancing** for high availability

---

**✅ Integration Status: COMPLETE**

The frontend-backend integration is fully functional and ready for production use. All Node.js functionality has been successfully migrated to the Python FastAPI backend with improved performance, type safety, and maintainability.
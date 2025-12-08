# Flood Prediction API - Python FastAPI Backend

A PostgreSQL-backed REST API for the Flood Prediction System, built with FastAPI.

## Features

- **Async PostgreSQL** - Uses asyncpg for high-performance database operations
- **PostGIS Support** - Full geospatial data support via GeoAlchemy2
- **Auto-generated API Docs** - Interactive Swagger UI at `/docs`
- **Type Safety** - Full Pydantic validation for requests and responses
- **Health Checks** - Built-in health endpoint for container orchestration

## Project Structure

```
python_backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection and session management
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── utils.py          # Utility functions
│   └── routers/
│       ├── __init__.py
│       ├── health.py     # Health check endpoints
│       ├── zones.py      # Zone management
│       ├── assets.py     # Asset management
│       ├── alerts.py     # Alert system
│       ├── resources.py  # Resource management
│       ├── risk.py       # Risk assessment, damage index, gauges
│       ├── communications.py  # Communication logs
│       ├── plans.py      # Response plans
│       └── admin.py      # Admin endpoints
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /api/zones` - Get all zones as GeoJSON
- `GET /api/assets` - Get critical assets
- `GET /api/alerts` - Get system alerts
- `POST /api/alerts/{id}/ack` - Acknowledge alert
- `GET /api/resources` - Get resources (crews, equipment, depots)
- `GET /api/risk` - Get risk assessments
- `GET /api/damage-index` - Get damage index data
- `GET /api/gauges` - Get gauge readings
- `GET /api/comms` - Get communications
- `POST /api/comms` - Create communication
- `GET /api/plan` - Get response plan
- `POST /api/plan/draft` - Create draft plan

### Admin Endpoints
- `GET/POST/PUT/DELETE /api/admin/users` - User management
- `GET/POST/PUT/DELETE /api/admin/thresholds/risk` - Risk thresholds
- `GET/POST/PUT/DELETE /api/admin/thresholds/gauges` - Gauge thresholds
- `GET/POST/PUT/DELETE /api/admin/alerts/rules` - Alert rules
- `GET /api/admin/resources/depots` - Admin depot view
- `GET /api/admin/resources/equipment` - Admin equipment view
- `GET /api/admin/resources/crews` - Admin crew view
- `PUT /api/admin/zones` - Update zones
- `GET /api/admin/export/{type}` - Export data

## Development

### Prerequisites
- Python 3.11+
- PostgreSQL with PostGIS extension
- Docker (optional)

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=flood_prediction
export DB_USER=flood_user
export DB_PASSWORD=flood_password
```

4. Run the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 18080 --reload
```

### Docker

Build and run with Docker Compose from the parent directory:
```bash
docker-compose up --build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 18080 | Server port |
| DB_HOST | localhost | PostgreSQL host |
| DB_PORT | 5432 | PostgreSQL port |
| DB_NAME | flood_prediction | Database name |
| DB_USER | flood_user | Database user |
| DB_PASSWORD | flood_password | Database password |
| DB_SSL | false | Enable SSL for database |
| DEBUG | false | Enable debug mode |

## API Documentation

Once the server is running, access the interactive API documentation:
- Swagger UI: http://localhost:18080/docs
- ReDoc: http://localhost:18080/redoc
- OpenAPI JSON: http://localhost:18080/api/openapi.json

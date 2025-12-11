# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a flood prediction system with three main components:

1. **Backend**: FastAPI service providing ML predictions and API endpoints
2. **Frontend**: React TypeScript application with interactive mapping
3. **Database**: PostgreSQL with PostGIS for geospatial data

The system uses XGBoost, Bayesian, and LSTM models to generate 1-3 day flood forecasts with uncertainty quantification via conformal prediction.

## Docker-First Development

**IMPORTANT**: All development, testing, and execution in this codebase is done through Docker. The system is designed to run entirely in containers - do not install Python dependencies or run services directly on the host machine.

### Full Stack Development
```bash
# Start all services (database, backend, frontend)
docker compose up -d

# View logs for all services
docker compose logs -f

# Stop all services
docker compose down
```

### Backend Development (in Docker)
```bash
# Backend runs in Docker container
# Access container shell for debugging
docker compose exec backend bash

# Run backend commands in container
docker compose exec backend python run.py

# Access API docs (when backend is running)
# http://localhost:8003/docs (Swagger)
# http://localhost:8003/redoc
```

### Frontend Development (in Docker)
```bash
# Frontend runs in Docker container
# Access container shell for debugging
docker compose exec frontend bash

# Frontend hot-reloads automatically in development mode
# Access at http://localhost:8001
```

### Database Operations (in Docker)
```bash
# Access database container
docker compose exec database psql -U flood_user -d flood_prediction

# Run scripts via backend container (has required dependencies)
docker compose exec backend python UI/scripts/load_raw_dataset.py --csv UI/database/demo_data/raw_dataset.csv
docker compose exec backend python UI/scripts/fetch_and_store_zip_geojson.py --output Data/zip_zones.geojson
```

### Model Training (in Docker)
```bash
# Model training runs in backend container with access to models directory
docker compose exec backend python Programs/06_train_models.py
```

## Key Architecture Patterns

### Backend Structure
- **Single endpoint design**: `/predict` handles all forecast horizons (1-3 days)
- **Dual data sources**: Database table or real-time APIs (USGS + weather)
- **Model ensemble**: XGBoost + Bayesian + LSTM with conformal calibration
- **Feature engineering**: Lag features, moving averages, precipitation windows

### Frontend-Backend Communication
- Frontend uses Vite proxy to route `/api` requests to backend
- State management via React Context and custom hooks
- Type-safe interfaces between frontend and API responses

### Database Schema
- `raw_data`: Daily hydrological inputs (precipitation, river levels, weather)
- `predictions`: Model forecasts with flood probabilities
- `zones`: Flood zone metadata with risk parameters
- `zip_zones` + `zip_geojson`: Geographic mapping for visualization

## Service Ports
- Frontend: 8001 (Nginx) or 5173 (Vite dev)
- Backend: 8003 (FastAPI)
- Database: 5439 (PostgreSQL with PostGIS)

## Model Locations
Trained models are stored in `Results/L{1,2,3}d/models/` relative to the `Programs/` directory.

## Key Configuration Files
- `backend/.env`: Database connection and API settings
- `docker-compose.yml`: Service orchestration and networking
- `frontend/vite.config.ts`: Build configuration and API proxy

## Development Workflow (Docker-Only)

1. **Start all services**: `docker compose up -d`
2. **Backend auto-reloads** on code changes in development mode (in container)
3. **Frontend hot-reloads** via Vite (in container)
4. **Database persists** data in Docker volumes
5. **Models are mounted** from `Results/` directory into backend container
6. **All testing** happens in the backend container via `docker compose exec`

### Container Access for Debugging
```bash
# Access individual service containers
docker compose exec backend bash    # Python/Debugging shell
docker compose exec frontend bash   # Node.js/Shell access
docker compose exec database psql -U flood_user -d flood_prediction  # DB shell
```

### Local Development Flow
- Edit code locally using your IDE
- Changes automatically sync into containers via volume mounts
- Services hot-reload within containers
- Run tests and commands via `docker compose exec`
- Never install dependencies directly on host machine

## API Endpoints
- `GET /predict`: Main prediction endpoint (1-3 day forecasts)
- `GET /zones`: Flood zone metadata
- `GET /zones-geo`: GeoJSON geometries for mapping
- `GET /rule-based/dispatch`: Resource allocation planning
- `GET /health`: Database connectivity check

## Testing Database Connection
```bash
curl http://localhost:8003/health
```

## Environment Variables
Key variables for development:
- `DB_HOST=localhost`, `DB_PORT=5439`
- `DB_NAME=flood_prediction`, `DB_USER=flood_user`, `DB_PASSWORD=flood_password`
- `API_HOST=0.0.0.0`, `API_PORT=8003`

## Testing (Docker-Only)

### Backend Testing Configuration
The backend uses pytest with the following configuration (from `backend/pytest.ini`):
- Test files: `tests/test_*.py`
- Minimum coverage: 80%
- Test markers: `unit`, `integration`, `slow`, `database`, `external`
- Coverage reports: terminal, HTML (`htmlcov/`), and XML

**IMPORTANT**: All tests must be run in the Docker container - they are designed to run with the container's environment and database connections.

### Test Commands (in Docker)
```bash
# Run all tests
docker compose exec backend python -m pytest

# Run with coverage reports
docker compose exec backend python -m pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend python -m pytest tests/test_api.py

# Run tests by marker
docker compose exec backend python -m pytest -m unit
docker compose exec backend python -m pytest -m integration
docker compose exec backend python -m pytest -m database

# Run tests without external dependencies
docker compose exec backend python -m pytest -m "not external"

# Run tests with specific output format
docker compose exec backend python -m pytest --tb=short -v
```
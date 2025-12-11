# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a flood prediction system with three main components:

1. **Backend**: FastAPI service providing ML predictions and API endpoints
2. **Frontend**: React TypeScript application with interactive mapping
3. **Database**: PostgreSQL with PostGIS for geospatial data

The system uses XGBoost, Bayesian, and LSTM models to generate 1-3 day flood forecasts with uncertainty quantification via conformal prediction.

## Common Development Commands

### Full Stack Development
```bash
# Start all services (database, backend, frontend)
docker compose up -d

# View logs for all services
docker compose logs -f

# Stop all services
docker compose down
```

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run in development mode (requires database running)
python run.py

# Access API docs
# http://localhost:8003/docs (Swagger)
# http://localhost:8003/redoc
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
```

### Database Operations
```bash
# Load sample data into database
python UI/scripts/load_raw_dataset.py --csv UI/database/demo_data/raw_dataset.csv

# Fetch ZIP code geojson data
python UI/scripts/fetch_and_store_zip_geojson.py --output Data/zip_zones.geojson
```

### Model Training
```bash
cd Programs
python 06_train_models.py  # Trains all 1, 2, 3-day models
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

## Development Workflow
1. Start services with `docker compose up -d`
2. Backend auto-reloads on code changes in development mode
3. Frontend hot-reloads via Vite
4. Database persists data in Docker volumes
5. Models are mounted from `Results/` directory into backend container

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
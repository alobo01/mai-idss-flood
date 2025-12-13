# Flood Prediction Backend

A sophisticated FastAPI-based microservice that provides real-time flood predictions, risk assessments, and resource allocation optimization for emergency response planning. This backend integrates advanced machine learning models with rule-based algorithms to deliver actionable intelligence for flood disaster management.

## 🌊 Overview

The backend serves as the computational core of the MAI IDSS (Intelligent Decision Support System), providing:

- **Multi-horizon flood predictions** (1-3 days ahead) using ensemble ML models
- **Uncertainty quantification** via conformal prediction intervals
- **Rule-based resource allocation** with fuzzy logic optimization
- **Real-time data integration** from USGS gauges and weather APIs
- **Geospatial analysis** with PostGIS-enabled PostgreSQL database

## 🏗 Architecture

### Core Components

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── db.py                      # Database connection and queries
│   ├── prediction_service.py      # ML model orchestration
│   ├── prediction/                # ML inference modules
│   │   ├── inference_api.py       # Core prediction engine
│   │   ├── feature_engineer.py    # Data preprocessing
│   │   └── data_fetcher.py        # Real-time API integration
│   └── rule_based/                # Resource allocation system
│       ├── allocations.py         # Resource distribution logic
│       ├── optimizer.py           # Linear programming optimization
│       ├── zones.py               # Zone management
│       └── zone_config.py         # Zone configurations
├── models/                        # Trained ML models
│   ├── L1d/                       # 1-day ahead models
│   ├── L2d/                       # 2-day ahead models
│   └── L3d/                       # 3-day ahead models
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container configuration
└── run.py                        # Development server
```

## 🤖 Machine Learning Pipeline

### Model Ensemble Architecture

The system employs a sophisticated ensemble of three complementary ML approaches:

#### 1. **XGBoost Quantile Regression**
- **Purpose**: Primary prediction engine with quantile outputs
- **Features**: Tree-based ensemble with robust handling of nonlinear relationships
- **Quantiles**: q10 (10th percentile), q50 (median), q90 (90th percentile)
- **Advantages**: Fast inference, interpretable feature importance

#### 2. **Bayesian Hierarchical Model**
- **Purpose**: Uncertainty quantification with probabilistic reasoning
- **Framework**: PyMC3/PyMC4 for Bayesian inference
- **Posterior Distribution**: Full predictive distribution sampling
- **Advantages**: Natural uncertainty representation, hierarchical structure

#### 3. **LSTM Neural Network**
- **Purpose**: Temporal pattern capture for sequential dependencies
- **Architecture**: Multi-layer LSTM with attention mechanisms
- **Quantiles**: Specialized quantile loss functions (q10, q50, q90)
- **Advantages**: Long-term dependency modeling, sequence learning

### Conformal Prediction System

**Uncertainty Calibration:**
- **Method**: Split conformal prediction with adaptive intervals
- **Coverage**: Guaranteed 80% prediction intervals under exchangeability
- **Adaptivity**: Width varies with prediction difficulty and data density
- **Calibration**: Continuously updated with incoming validation data

## 🌐 API Endpoints

### Core Prediction Services

#### `GET /predict`
Generate multi-horizon flood predictions with uncertainty quantification

**Parameters:**
- `use_real_time_api` (bool): Use live data vs. database
- `lead_times` (list): [1, 2, 3] day horizons

**Response:**
```json
{
  "timestamp": "2025-12-11T12:00:00Z",
  "use_real_time_api": false,
  "data_source": "database (raw_data table)",
  "predictions": [
    {
      "lead_time_days": 1,
      "forecast_date": "2025-12-12",
      "forecast": {
        "median": 23.45,
        "xgboost": 23.1,
        "bayesian": 23.8,
        "lstm": 23.4
      },
      "prediction_interval_80pct": {
        "lower": 22.1,
        "median": 23.45,
        "upper": 24.8,
        "width": 2.7
      },
      "flood_risk": {
        "probability": 0.15,
        "threshold_ft": 30.0,
        "risk_level": "MODERATE",
        "risk_indicator": "🟡"
      }
    }
  ]
}
```

#### `GET /rule-based/dispatch`
Optimize resource allocation based on flood risk predictions

**Parameters:**
- `total_units` (int): Total available response units (1-200)
- `mode` (str): Allocation mode (`crisp|fuzzy|proportional|optimized`)
- `lead_time` (int): Prediction horizon (1-7 days)
- `max_units_per_zone` (int, optional): Maximum units per zone
- `use_optimizer` (bool): Use linear programming optimization

#### Additional Endpoints
- `GET /raw-data` - Retrieve recent hydrological observations
- `GET /zones` - Zone metadata for UI components
- `GET /zones-geo` - GeoJSON geometries for map visualization
- `GET /resource-types` - Available emergency resource types
- `PUT /resource-types/capacities` - Update resource capacities
- `GET /health` - Database connectivity check

## 🗄️ Database Setup from Scratch

### Prerequisites
- Docker and Docker Compose installed
- PostgreSQL client tools (optional)

### Step 1: Initialize Database Schema

**Using Docker Compose (Recommended):**
```bash
cd UI
docker compose up -d database
```

The database initialization script automatically runs:
```bash
# This script runs automatically when the database container starts
docker compose exec database psql -U flood_user -d flood_prediction -f /docker-entrypoint-initdb.d/01-schema.sql
```

**Manual Schema Creation:**
```bash
# Connect to the database
docker compose exec database psql -U flood_user -d flood_prediction

# Run the schema file
\i /docker-entrypoint-initdb.d/01-schema.sql
```

### Step 2: Database Schema Overview

The database contains the following key tables:

#### Core Tables

**raw_data**: Daily hydrological observations
```sql
CREATE TABLE raw_data (
    date DATE PRIMARY KEY,
    daily_precip NUMERIC(5,2),
    daily_temp_avg NUMERIC(5,2),
    daily_snowfall NUMERIC(5,2),
    daily_humidity NUMERIC(5,2),
    daily_wind NUMERIC(5,2),
    soil_deep_30d NUMERIC(5,2),
    target_level_max NUMERIC(6,2),
    hermann_level NUMERIC(6,2),
    grafton_level NUMERIC(6,2)
);
```

**predictions**: Model forecast storage
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    forecast_date DATE,
    lead_time_days INTEGER,
    model_version VARCHAR(50),
    predicted_level NUMERIC(6,2),
    lower_bound_80 NUMERIC(6,2),
    upper_bound_80 NUMERIC(6,2),
    flood_probability NUMERIC(5,4),
    model_type VARCHAR(20)
);
```

**zones**: Geographic and demographic data
```sql
CREATE TABLE zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    river_proximity NUMERIC(3,2),
    elevation_risk NUMERIC(3,2),
    pop_density NUMERIC(8,2),
    crit_infra_score NUMERIC(3,2),
    hospital_count INTEGER,
    critical_infra BOOLEAN
);
```

**zip_zones**: ZIP code to zone mapping
```sql
CREATE TABLE zip_zones (
    zip_code VARCHAR(10) PRIMARY KEY,
    zone_id VARCHAR(50) REFERENCES zones(zone_id)
);
```

**zip_geojson**: ZIP code geographic boundaries
```sql
CREATE TABLE zip_geojson (
    zip_code VARCHAR(10) PRIMARY KEY,
    geojson JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**resource_types**: Emergency resource definitions
```sql
CREATE TABLE resource_types (
    resource_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    icon VARCHAR(50),
    capacity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Step 3: Load Base Data

#### Load Demo Dataset
```bash
cd UI
python scripts/load_raw_dataset.py --csv database/demo_data/raw_dataset.csv
```

**What this script does:**
1. Loads historical hydrological data (2018-2022)
2. Populates the `raw_data` table with daily observations
3. Includes St. Louis, Hermann, and Grafton gauge readings
4. Adds weather data (precipitation, temperature, etc.)

#### Load Zone Definitions
```bash
# Load zone metadata
python scripts/load_zones.py --file database/demo_data/zones.csv

# Load ZIP code mappings
python scripts/load_zip_mappings.py --file database/demo_data/zip_zones.csv
```

#### Load ZIP Code Geometries
```bash
# Fetch ZIP code boundaries from external API
python scripts/fetch_and_store_zip_geojson.py --output Data/zip_zones.geojson

# Or load from existing file
python scripts/load_geojson.py --file Data/zip_zones.geojson
```

#### Load Resource Types
```bash
# Load default emergency resource types
python scripts/load_resources.py --file database/demo_data/resources.csv
```

### Step 4: Verify Data Loading

#### Check Database Contents
```bash
# Connect to database
docker compose exec database psql -U flood_user -d flood_prediction

# Check row counts
SELECT
  (SELECT COUNT(*) FROM raw_data) as raw_data_count,
  (SELECT COUNT(*) FROM zones) as zones_count,
  (SELECT COUNT(*) FROM zip_zones) as zip_zones_count,
  (SELECT COUNT(*) FROM zip_geojson) as geojson_count,
  (SELECT COUNT(*) FROM resource_types) as resource_types_count;
```

#### Sample Data Queries
```sql
-- Check recent raw data
SELECT date, target_level_max, daily_precip
FROM raw_data
ORDER BY date DESC
LIMIT 10;

-- Check zone definitions
SELECT zone_id, name, pop_density, critical_infra
FROM zones
ORDER BY zone_id;

-- Check resource types
SELECT resource_id, name, capacity
FROM resource_types
ORDER BY resource_id;
```

## 📊 Data Population Strategy

### Automated Data Loading

**Use the comprehensive setup script:**
```bash
cd UI
# This script handles all data loading in sequence
python scripts/setup_database.py --all

# Or run individual steps
python scripts/setup_database.py --raw-data
python scripts/setup_database.py --zones
python scripts/setup_database.py --geojson
python scripts/setup_database.py --resources
```

### Data Sources

#### Historical Hydrological Data
- **USGS Gauges**: Real-time river level data
  - St. Louis (07010000): Primary monitoring station
  - Hermann (06934500): Upstream indicator
  - Grafton (05587450): Additional upstream signal

#### Weather Data
- **Open-Meteo API**: Historical weather conditions
- **NOAA**: Climate data archives
- **Local Weather Stations**: Ground truth measurements

#### Geographic Data
- **USPS ZIP Code Database**: ZIP code boundaries
- **Census Data**: Population and demographic information
- **FEMA Flood Zones**: Historical flood risk areas

#### Resource Data
- **Emergency Management**: Local resource inventories
- **Hospital Database**: Healthcare facility locations
- **Infrastructure Maps**: Critical asset locations

### Data Validation

#### Quality Checks
```bash
# Run data validation script
python scripts/validate_data.py --all

# Check for data gaps
python scripts/validate_data.py --gaps

# Validate geographic data
python scripts/validate_data.py --geojson
```

#### Common Issues and Solutions

**Missing Dates in raw_data:**
```sql
-- Find missing dates
SELECT generate_series(
  (SELECT MIN(date) FROM raw_data),
  (SELECT MAX(date) FROM raw_data),
  '1 day'::interval
) AS all_dates
EXCEPT
SELECT date FROM raw_data;
```

**Invalid ZIP Codes:**
```sql
-- Find ZIP codes without geometry
SELECT zz.zip_code, zz.zone_id
FROM zip_zones zz
LEFT JOIN zip_geojson zg ON zz.zip_code = zg.zip_code
WHERE zg.zip_code IS NULL;
```

**Zero or Negative Populations:**
```sql
-- Find zones with population issues
SELECT zone_id, name, pop_density
FROM zones
WHERE pop_density <= 0;
```

## 🔧 Configuration & Deployment

### Environment Variables

**Database Configuration:**
```bash
DB_HOST=localhost
DB_PORT=5439
DB_NAME=flood_prediction
DB_USER=flood_user
DB_PASSWORD=flood_password
```

**API Configuration:**
```bash
API_HOST=0.0.0.0
API_PORT=8003
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

**Model Configuration:**
```bash
MODEL_BASE_DIR=/app/models
FLOOD_THRESHOLD_FT=30.0
PREDICTION_INTERVAL_COVERAGE=0.80
```

### Setup Instructions

### 1. Install Dependencies

```bash
cd UI/backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and adjust if needed:

```bash
cp .env.example .env
```

Default configuration (matches docker-compose):
```env
DB_HOST=localhost
DB_PORT=5439
DB_NAME=flood_prediction
DB_USER=flood_user
DB_PASSWORD=flood_password
API_HOST=0.0.0.0
API_PORT=8003
```

### 3. Database Setup

**Option A: Docker (Recommended)**
```bash
cd UI
docker compose up -d
```

This will:
- Start PostgreSQL with PostGIS extension
- Automatically create the database schema
- Initialize with base data if available

**Option B: Manual Database Setup**
```bash
# Install PostgreSQL with PostGIS
sudo apt-get install postgresql postgresql-contrib postgis

# Create database
sudo -u postgres createdb flood_prediction

# Create user
sudo -u postgres createuser --interactive flood_user

# Enable PostGIS extension
sudo -u postgres psql -d flood_prediction -c "CREATE EXTENSION postgis;"

# Load schema manually
psql -U flood_user -d flood_prediction -f database/init/01-schema.sql
```

### 4. Load Initial Data

```bash
cd UI
# Load all demo data at once
python scripts/setup_database.py --all

# Or load individual datasets
python scripts/load_raw_dataset.py --csv database/demo_data/raw_dataset.csv
python scripts/load_zones.py --file database/demo_data/zones.csv
python scripts/load_geojson.py --file Data/zip_zones.geojson
python scripts/load_resources.py --file database/demo_data/resources.csv
```

### 5. Train ML Models

```bash
cd Programs
python 06_train_models.py  # Trains all 1, 2, 3-day models
```

## 🚀 Running the Application

### Docker Compose (Recommended)

```bash
cd UI
docker compose up -d
```

This will start:
- **Database**: PostgreSQL with PostGIS on port 5439
- **Backend**: FastAPI service on port 8003
- **Frontend**: Nginx on port 8001 (or Vite dev server on 5173)

### Development Mode

```bash
cd UI/backend
python run.py
```

The API will start at `http://localhost:8003` with auto-reload enabled.

### API Documentation
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

## 🧪 Testing the Setup

### Health Checks

```bash
# Check API health
curl http://localhost:8003/health

# Check database connectivity
curl http://localhost:8003/health

# Test prediction endpoint
curl http://localhost:8003/predict

# Test resource allocation
curl "http://localhost:8003/rule-based/dispatch?total_units=20&mode=fuzzy"
```

### Data Verification

```bash
# Check raw data
curl http://localhost:8003/raw-data

# Check zones
curl http://localhost:8003/zones

# Check zone geometries
curl http://localhost:8003/zones-geo

# Check resources
curl http://localhost:8003/resource-types
```

## 📊 Production Deployment

### Docker Configuration

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY models/ ./models/
COPY run.py .

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Start application
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Environment Configuration

**Production .env:**
```env
# Database
DB_HOST=database-service
DB_PORT=5432
DB_NAME=flood_prediction_prod
DB_USER=prod_user
DB_PASSWORD=secure_password_here

# API
API_HOST=0.0.0.0
API_PORT=8003
CORS_ORIGINS=["https://yourdomain.com"]

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

## 🔒 Security & Performance

### API Security

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/predict")
@limiter.limit("10/minute")  # 10 predictions per minute per IP
async def predict(request: Request):
    # Prediction logic
    pass
```

**Input Validation:**
- All endpoints use Pydantic models for validation
- SQL injection prevention with parameterized queries
- XSS protection with proper output encoding

### Performance Optimization

**Database Optimization:**
```sql
-- Indexes for performance
CREATE INDEX idx_raw_data_date ON raw_data(date DESC);
CREATE INDEX idx_predictions_forecast_date ON predictions(forecast_date);
CREATE INDEX idx_zones_zone_id ON zones(zone_id);
CREATE INDEX idx_zip_geojson_zip_code ON zip_geojson(zip_code);
```

**Caching Strategy:**
- Redis for API response caching
- Model prediction caching for identical inputs
- Database query result caching

## 🔍 Troubleshooting

### Common Issues

**Database Connection Fails:**
```bash
# Check if database is running
docker compose ps database

# Check database logs
docker compose logs database

# Test connection manually
docker compose exec database psql -U flood_user -d flood_prediction -c "SELECT 1;"
```

**Missing Model Files:**
```bash
# Check model directory
ls -la models/L1d/models/

# Train missing models
cd Programs
python 06_train_models.py

# Check model files exist
find models/ -name "*.pkl" -o -name "*.json" -o -name "*.h5"
```

**Empty Database:**
```bash
# Check row counts
docker compose exec database psql -U flood_user -d flood_prediction -c "
  SELECT
    (SELECT COUNT(*) FROM raw_data) as raw_data,
    (SELECT COUNT(*) FROM zones) as zones,
    (SELECT COUNT(*) FROM zip_zones) as zip_zones;
"

# Load demo data if needed
cd UI
python scripts/setup_database.py --all
```

**API Response Errors:**
```bash
# Check API logs
docker compose logs backend

# Test individual endpoints
curl -v http://localhost:8003/health
curl -v http://localhost:8003/predict
```

### Performance Issues

**Slow API Responses:**
```bash
# Check database query performance
docker compose exec database psql -U flood_user -d flood_prediction -c "
EXPLAIN ANALYZE SELECT * FROM raw_data ORDER BY date DESC LIMIT 30;
"

# Monitor resource usage
docker stats
```

**Memory Issues:**
```bash
# Check container memory usage
docker compose exec backend python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

---

**Built with precision and reliability for emergency operations**
**MAI IDSS - Advanced Flood Prediction System**

## Running the API

### Option 1: Docker (Recommended)

Run the entire stack (database + backend) with Docker Compose:

```bash
cd UI
docker compose up -d
```

The API will be available at `http://localhost:8000`.

To view logs:
```bash
docker compose logs -f backend
```

To stop:
```bash
docker compose down
```

### Option 2: Development Mode (Local)

```bash
cd UI/backend
python run.py
```

The API will start at `http://localhost:8000` with auto-reload enabled.

**Note:** Requires local PostgreSQL running (see Setup section).

### Interactive Docs

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### `GET /`
Health check - returns API status and version.

**Response:**
```json
{
  "status": "healthy",
  "message": "Flood Prediction API is running",
  "version": "1.0.0"
}
```

### `GET /predict`
Generate flood predictions for next 1-3 days.

**Query Parameters:**
- `use_real_time_api` (boolean, default: `false`): 
  - `false` → Use database `raw_data` table
  - `true` → Fetch live data from USGS and weather APIs

**Response Example:**
```json
{
  "timestamp": "2025-12-10T12:00:00",
  "use_real_time_api": false,
  "data_source": "database (raw_data table)",
  "predictions": [
    {
      "lead_time_days": 1,
      "forecast_date": "2025-12-11",
      "forecast": {
        "median": 12.5,
        "xgboost": 12.3,
        "bayesian": 12.6,
        "lstm": 12.4
      },
      "conformal_interval_80pct": {
        "lower": 11.8,
        "median": 12.5,
        "upper": 13.2,
        "width": 1.4
      },
      "flood_risk": {
        "probability": 0.05,
        "threshold_ft": 30.0,
        "risk_level": "LOW",
        "risk_indicator": "🟢"
      }
    },
    {
      "lead_time_days": 2,
      "forecast_date": "2025-12-12",
      "forecast": { ... },
      "conformal_interval_80pct": { ... },
      "flood_risk": { ... }
    },
    {
      "lead_time_days": 3,
      "forecast_date": "2025-12-13",
      "forecast": { ... },
      "conformal_interval_80pct": { ... },
      "flood_risk": { ... }
    }
  ]
}
```

### `GET /health`
Database connectivity check.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-10T12:00:00"
}
```

## Usage Examples

### Using database data (default):
```bash
curl http://localhost:8000/predict
```

### Using real-time APIs:
```bash
curl "http://localhost:8000/predict?use_real_time_api=true"
```

### Using Python requests:
```python
import requests

# Database mode
response = requests.get("http://localhost:8000/predict")
predictions = response.json()

# Real-time API mode
response = requests.get(
    "http://localhost:8000/predict",
    params={"use_real_time_api": True}
)
predictions = response.json()

# Extract 2-day forecast
forecast_2day = predictions["predictions"][1]
print(f"2-day forecast: {forecast_2day['forecast']['median']} ft")
print(f"Flood risk: {forecast_2day['flood_risk']['risk_level']}")
```

## How It Works

1. **Data Retrieval**:
   - `use_real_time_api=false`: Queries last 30 days from `raw_data` table
   - `use_real_time_api=true`: Fetches live data from USGS and Open-Meteo APIs

2. **Feature Engineering**:
   - Creates lag features, moving averages, precipitation windows
   - Uses `FeatureEngineer` class from `Programs/feature_engineer.py`

3. **Prediction**:
   - Loads trained models from `Results/L{1,2,3}d/models/`
   - Runs XGBoost, Bayesian, and LSTM models in parallel
   - Ensembles predictions using min/median/max quantiles
   - Applies conformal calibration for uncertainty

4. **Response**:
   - Returns predictions for all 3 lead times
   - Each includes median forecast, uncertainty intervals, flood risk

## Dependencies

Key packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `psycopg2-binary` - PostgreSQL driver
- `pandas`, `numpy` - Data processing
- `xgboost`, `tensorflow`, `scikit-learn` - ML models
- `python-dotenv` - Environment management

See `requirements.txt` for full list with versions.

## Troubleshooting

### "Import could not be resolved" errors
These are lint warnings because models aren't installed yet. They'll resolve after running `pip install -r requirements.txt`.

### Database connection fails
- Ensure Docker containers are running: `docker compose up -d`
- Check `.env` file matches your database configuration
- Test connection: `curl http://localhost:8000/health`

### "Insufficient data" error
Database needs at least 30 days of data. Load demo data:
```bash
python UI/scripts/load_raw_dataset.py --csv UI/database/demo_data/raw_dataset.csv
```

### Model files not found
Ensure models are trained:
```bash
cd Programs
python 06_train_models.py  # Trains all 1, 2, 3-day models
```

### Real-time API fails
Check network connectivity and API availability:
- USGS: https://waterservices.usgs.gov/
- Open-Meteo: https://open-meteo.com/

## Docker Configuration

The backend is containerized and integrated with the postgres service:

### docker-compose.yml Structure
```yaml
services:
  postgres:
    # Database service (port 5439)
  
  backend:
    # FastAPI service (port 8000)
    # Automatically connects to postgres
    # Mounts Programs/, Results/, Data/ directories
```

### Key Features
- **Volume mounts**: Access to trained models (`Results/`) and data (`Programs/`, `Data/`)
- **Health checks**: Automatic service health monitoring
- **Networking**: Services communicate on shared `flood-network`
- **Dependencies**: Backend waits for postgres to be healthy before starting

### Building and Running

Build and start all services:
```bash
cd UI
docker compose up --build -d
```

Rebuild only backend:
```bash
docker compose build backend
docker compose up -d backend
```

View backend logs:
```bash
docker compose logs -f backend
```

Access backend shell:
```bash
docker compose exec backend bash
```

## Production Deployment

For production use:

1. **Security**:
   - Set specific CORS origins in `main.py`
   - Use environment variables for secrets
   - Enable HTTPS with reverse proxy (nginx/traefik)
   - Update docker-compose with production credentials

2. **Performance**:
   - Use production ASGI server (e.g., `gunicorn -k uvicorn.workers.UvicornWorker`)
   - Add caching for repeated requests
   - Consider model serving optimizations
   - Adjust resource limits in docker-compose

3. **Monitoring**:
   - Add logging aggregation (ELK stack, Loki)
   - Set up health check monitoring (Prometheus)
   - Track prediction latency and errors
   - Use docker health checks for auto-restart

## License

Part of the IDSS flood prediction project.

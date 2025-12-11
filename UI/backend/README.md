# Flood Prediction API Backend

FastAPI backend for the flood prediction system. Provides a `/predict` endpoint that generates 1-3 day river level forecasts using trained ML models.

## Features

- **Single prediction endpoint** (`/predict`) that returns 1, 2, and 3-day forecasts
- **Dual data sources**: Use database or real-time APIs (USGS + weather)
- **Automatic model loading**: Loads pre-trained XGBoost, Bayesian, and LSTM models
- **Uncertainty quantification**: Conformal prediction intervals
- **Flood risk assessment**: Probability and risk level for each forecast

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app and routes
│   ├── db.py                   # Database connection and queries
│   └── prediction_service.py   # Prediction logic using FloodPredictorV2
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── run.py                     # Development server launcher
```

## Setup

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
API_PORT=8000
```

### 3. Ensure Database is Running

Make sure the PostgreSQL database is up:

```bash
cd UI
docker compose up -d
```

### 4. Load Sample Data (Optional)

If database is empty, load demo data:

```bash
python UI/scripts/load_raw_dataset.py --csv UI/database/demo_data/raw_dataset.csv
```

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

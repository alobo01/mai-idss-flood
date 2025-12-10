# Level Prediction Package

A self-contained, production-ready Python package for flood level prediction in the St. Louis region.

## Features

- **Real-time Data**: Automatically fetches current river levels (USGS) and weather data (Open-Meteo)
- **Ensemble Models**: Combines XGBoost, Bayesian Ridge, and LSTM predictions
- **Uncertainty Quantification**: Provides prediction intervals and conformal intervals
- **Risk Assessment**: Calculates flood probabilities and risk levels
- **Easy Installation**: Install once, import anywhere

## Installation

### From local directory:
```bash
pip install -e /path/to/level_prediction
```

### Or install directly:
```bash
cd /path/to/level_prediction
pip install .
```

## Quick Start

```python
from level_prediction import FloodPredictor

# Create predictor for 1-day forecast
predictor = FloodPredictor(lead_time_days=1)

# Option 1: Use live data from APIs
result = predictor.predict_live()

# Option 2: Use your own data
import pandas as pd
data = pd.read_csv('river_data.csv')
result = predictor.predict_from_raw_data(data)

# Access results
print(f"Forecast: {result['forecast']['median']:.2f} ft")
print(f"Risk Level: {result['flood_risk']['risk_level']}")
print(f"Flood Probability: {result['flood_risk']['probability']:.1%}")
```

## Data Format

If providing your own data, ensure it contains these columns:

| Column | Description | Units |
|--------|-------------|-------|
| `date` | Date of observation | YYYY-MM-DD |
| `target_level_max` | St. Louis river level | feet |
| `hermann_level` | Missouri River level at Hermann | feet |
| `grafton_level` | Mississippi River level at Grafton | feet |
| `daily_precip` | Daily precipitation | mm |
| `daily_temp_avg` | Daily average temperature | °C |
| `daily_snowfall` | Daily snowfall | mm |
| `daily_humidity` | Daily average humidity | % |
| `daily_wind` | Daily average wind speed | m/s |
| `soil_deep_30d` | Soil moisture (28-100cm depth) | m³/m³ |

**Minimum data requirement**: 30 days of historical data

## API Response

The predictor returns a dictionary with:

```python
{
    'timestamp': '2025-12-10T15:30:45.123456',
    'lead_time_days': 1,
    
    'current_conditions': {
        'date': '2025-12-10',
        'current_level_st_louis': 27.45,
        'current_level_hermann': 24.12,
        'current_level_grafton': 28.67,
        'recent_precip_7d': 15.2,
    },
    
    'forecast': {
        'median': 28.50,      # Ensemble median
        'xgboost': 28.45,
        'bayesian': 28.55,
        'lstm': 28.50,
    },
    
    'prediction_interval_80pct': {
        'lower': 27.10,
        'upper': 29.90,
        'width': 2.80,
    },
    
    'conformal_interval_80pct': {
        'lower': 26.95,
        'median': 28.50,
        'upper': 30.05,
        'width': 3.10,
    },
    
    'flood_risk': {
        'probability': 0.25,
        'threshold_ft': 30.0,
        'risk_level': 'LOW',
        'risk_indicator': '🟢',
    },
}
```

## Models

The package includes pre-trained ensemble models for:
- **1-day forecast** (L1d)
- **2-day forecast** (L2d)
- **3-day forecast** (L3d)

Models are stored in `level_prediction/models/` with full quantile predictions (10th, 50th, 90th percentiles).

## Advanced Usage

### Custom model directory:
```python
predictor = FloodPredictor(
    lead_time_days=1,
    model_dir='/path/to/custom/models'
)
```

### Fetch data separately:
```python
from level_prediction import DataFetcher, FeatureEngineer

fetcher = DataFetcher()
data = fetcher.fetch_last_30_days()

engineer = FeatureEngineer(lead_time_days=1)
features = engineer.create_features(data)
```

## Requirements

- Python >= 3.9
- pandas >= 2.0.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- xgboost >= 1.7.6
- tensorflow >= 2.15.0
- joblib >= 1.3.0
- scipy >= 1.11.0
- requests >= 2.31.0

## Package Structure

```
level_prediction/
├── __init__.py              # Package exports
├── config.py                # Configuration and constants
├── predictor.py             # Main FloodPredictor class
├── feature_engineer.py      # Feature engineering
├── data_fetcher.py          # Real-time data fetching
├── setup.py                 # Installation script
├── README.md                # This file
└── models/
    ├── L1d/                 # 1-day forecast models
    ├── L2d/                 # 2-day forecast models
    └── L3d/                 # 3-day forecast models
```

## Data Sources

- **River Levels**: USGS National Water Information System
  - Mississippi River at St. Louis (Station 07010000)
  - Missouri River at Hermann (Station 06934500)
  - Mississippi River at Grafton (Station 05587450)

- **Weather Data**: Open-Meteo API
  - Precipitation, temperature, snowfall, humidity, wind speed
  - Soil moisture

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please contact the IDSS Flood Prediction Team.

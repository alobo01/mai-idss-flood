"""
Installation and setup instructions for level_prediction package

This file explains how to use and install the level_prediction package.
"""

# ============================================================================
# INSTALLATION OPTIONS
# ============================================================================

## Option 1: Install from source (development mode)
# This allows you to modify the code and test changes immediately
# Run from the level_prediction directory:
#   pip install -e .

## Option 2: Install as regular package
# Run from the level_prediction directory:
#   pip install .

## Option 3: Install with requirements file
# From anywhere:
#   pip install -r /path/to/level_prediction/requirements.txt
#   export PYTHONPATH="/path/to/level_prediction:$PYTHONPATH"

# ============================================================================
# BASIC USAGE
# ============================================================================

from level_prediction import FloodPredictor

# Create a predictor instance
predictor = FloodPredictor(lead_time_days=1)

# Generate prediction from live data
result = predictor.predict_live()

# Or use your own data
import pandas as pd
data = pd.read_csv('your_data.csv')
result = predictor.predict_from_raw_data(data)

# ============================================================================
# ACCESSING PREDICTIONS
# ============================================================================

# Forecast value (ensemble median)
forecast = result['forecast']['median']

# Flood risk assessment
risk_level = result['flood_risk']['risk_level']  # 'LOW', 'MODERATE', 'HIGH'
flood_prob = result['flood_risk']['probability']

# Prediction intervals for uncertainty quantification
pi_lower = result['prediction_interval_80pct']['lower']
pi_upper = result['prediction_interval_80pct']['upper']

# Conformal intervals (more conservative estimates)
ci_lower = result['conformal_interval_80pct']['lower']
ci_upper = result['conformal_interval_80pct']['upper']

# Current conditions
current_level = result['current_conditions']['current_level_st_louis']

# ============================================================================
# DIFFERENT LEAD TIMES
# ============================================================================

# 1-day forecast
predictor_1d = FloodPredictor(lead_time_days=1)

# 2-day forecast
predictor_2d = FloodPredictor(lead_time_days=2)

# 3-day forecast
predictor_3d = FloodPredictor(lead_time_days=3)

# ============================================================================
# DATA REQUIREMENTS
# ============================================================================

# Your data must have these columns:
required_columns = [
    'date',                  # YYYY-MM-DD format
    'target_level_max',      # St. Louis level (feet)
    'hermann_level',         # Hermann level (feet)
    'grafton_level',         # Grafton level (feet)
    'daily_precip',          # Precipitation (mm)
    'daily_temp_avg',        # Temperature (°C)
    'daily_snowfall',        # Snowfall (mm)
    'daily_humidity',        # Humidity (%)
    'daily_wind',            # Wind speed (m/s)
    'soil_deep_30d',         # Soil moisture (m³/m³)
]

# Minimum 30 days of data required for prediction

# ============================================================================
# PACKAGE STRUCTURE
# ============================================================================

"""
level_prediction/
├── __init__.py                 # Main package exports
├── config.py                   # Configuration and constants
├── predictor.py                # FloodPredictor class
├── feature_engineer.py         # FeatureEngineer class
├── data_fetcher.py             # DataFetcher class
├── setup.py                    # Installation script
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
├── INSTALL.md                  # This file
├── models/
│   ├── L1d/                    # 1-day forecast models
│   │   ├── xgb_q10.json
│   │   ├── xgb_q50.json
│   │   ├── xgb_q90.json
│   │   ├── bayes_model.pkl
│   │   ├── bayes_scaler.pkl
│   │   ├── lstm_q10.h5
│   │   ├── lstm_q50.h5
│   │   ├── lstm_q90.h5
│   │   ├── lstm_scaler_x.pkl
│   │   ├── lstm_scaler_y.pkl
│   │   └── calibration_info.pkl
│   ├── L2d/                    # 2-day forecast models
│   └── L3d/                    # 3-day forecast models
└── examples/
    ├── example_live_data.py            # Using live API data
    ├── example_custom_data.py          # Using your own data
    └── example_compare_lead_times.py   # Comparing forecasts
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Issue: ModuleNotFoundError: No module named 'level_prediction'
# Solution: Make sure the package is installed:
#   pip install -e /path/to/level_prediction
# Or add to PYTHONPATH:
#   export PYTHONPATH="/path/to/level_prediction:$PYTHONPATH"

# Issue: FileNotFoundError: Model files not found
# Solution: Verify models are in the models/ subdirectory and installation included them

# Issue: Data format errors
# Solution: Check your data has all required columns in the right format

# Issue: API timeouts
# Solution: Check internet connection; USGS and Open-Meteo APIs may be temporarily unavailable

# ============================================================================

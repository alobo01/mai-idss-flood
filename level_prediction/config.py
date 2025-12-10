"""
Configuration module for level_prediction package
"""

import os
from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent

# Model paths
MODELS_ROOT = PACKAGE_ROOT / "models"
L1D_MODEL_PATH = MODELS_ROOT / "L1d"
L2D_MODEL_PATH = MODELS_ROOT / "L2d"
L3D_MODEL_PATH = MODELS_ROOT / "L3d"

# Model configuration
AVAILABLE_LEAD_TIMES = [1, 2, 3]
DEFAULT_LEAD_TIME = 1

# Flood threshold (feet)
FLOOD_THRESHOLD_FT = 30.0

# Station configuration
STATIONS = {
    'target': {
        'id': '07010000',
        'name': 'Mississippi River at St. Louis, MO',
        'lat': 38.6270,
        'lon': -90.1994
    },
    'hermann': {
        'id': '06934500',
        'name': 'Missouri River at Hermann, MO',
        'lat': 38.7098,
        'lon': -91.4385
    },
    'grafton': {
        'id': '05587450',
        'name': 'Mississippi River at Grafton, IL',
        'lat': 38.9680,
        'lon': -90.4290
    },
}

# Weather data location (St. Louis)
WEATHER_LAT = 38.6270
WEATHER_LON = -90.1994

# Feature generation
MIN_DATA_POINTS = 30  # Minimum days of data needed

# Risk thresholds
RISK_THRESHOLDS = {
    'LOW': 0.3,
    'MODERATE': 0.7,
}

# Risk colors
RISK_COLORS = {
    'LOW': '🟢',
    'MODERATE': '🟡',
    'HIGH': '🔴',
}

def get_model_path(lead_time_days: int) -> Path:
    """Get the model directory for a specific lead time"""
    if lead_time_days == 1:
        return L1D_MODEL_PATH
    elif lead_time_days == 2:
        return L2D_MODEL_PATH
    elif lead_time_days == 3:
        return L3D_MODEL_PATH
    else:
        raise ValueError(f"Unsupported lead time: {lead_time_days}. Available: {AVAILABLE_LEAD_TIMES}")

def verify_models_exist(lead_time_days: int) -> bool:
    """Check if all required model files exist"""
    model_path = get_model_path(lead_time_days)
    
    required_files = [
        'xgb_q10.json',
        'xgb_q50.json',
        'xgb_q90.json',
        'bayes_model.pkl',
        'bayes_scaler.pkl',
        'lstm_q10.h5',
        'lstm_q50.h5',
        'lstm_q90.h5',
        'lstm_scaler_x.pkl',
        'lstm_scaler_y.pkl',
        'calibration_info.pkl',
    ]
    
    all_exist = all((model_path / f).exists() for f in required_files)
    return all_exist

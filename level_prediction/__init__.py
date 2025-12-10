"""
Level Prediction Package - Self-contained flood level prediction for St. Louis

A complete, importable package for flood level prediction including:
- Real-time data fetching from USGS and weather APIs
- Feature engineering for time series prediction
- Ensemble prediction using XGBoost, Bayesian Ridge, and LSTM models
- Uncertainty quantification with conformal intervals
- Flood risk assessment

Usage:
    from level_prediction import FloodPredictor
    
    predictor = FloodPredictor(lead_time_days=1)
    result = predictor.predict_live()
    
    # Or with your own data:
    import pandas as pd
    data = pd.read_csv('river_data.csv')
    result = predictor.predict_from_raw_data(data)
"""

__version__ = "1.0.0"
__author__ = "IDSS Flood Prediction Team"

from .predictor import FloodPredictor
from .data_fetcher import DataFetcher, get_latest_data
from .feature_engineer import FeatureEngineer

__all__ = [
    'FloodPredictor',
    'DataFetcher',
    'FeatureEngineer',
    'get_latest_data',
]

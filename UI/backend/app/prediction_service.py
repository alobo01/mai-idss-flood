"""
Prediction service - integrates FloodPredictorV2 with database/API
"""
import sys
import os
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path

from .prediction.inference_api import FloodPredictorV2
from .db import insert_prediction, get_prediction

logger = logging.getLogger(__name__)

MODEL_BASE_DIR = Path(__file__).resolve().parent.parent / "models"


def _model_dir_for_lead(lead_time: int) -> Path:
    """Return the model directory for a given lead time."""
    return MODEL_BASE_DIR / f"L{lead_time}d" / "models"


def _missing_model_files(lead_time: int) -> List[str]:
    """Return the list of missing model files for a given lead time."""
    model_dir = _model_dir_for_lead(lead_time)
    required_files = [
        "xgb_q10.json",
        "xgb_q50.json",
        "xgb_q90.json",
        "bayes_model.pkl",
        "bayes_scaler.pkl",
        "lstm_q10.h5",
        "lstm_q50.h5",
        "lstm_q90.h5",
        "lstm_scaler_x.pkl",
        "lstm_scaler_y.pkl",
    ]

    missing = []
    for fname in required_files:
        fpath = model_dir / fname
        if not fpath.exists():
            missing.append(str(fpath))
    return missing


def _naive_fallback_prediction(raw_data: pd.DataFrame, lead_time: int) -> dict:
    """Produce a simple fallback prediction when trained models are unavailable.

    It uses the last observed `target_level_max` as the median forecast and
    sets a small uncertainty window. This is intentionally simple so the
    service remains operational until proper models are available.
    """
    last = raw_data.sort_values('date').iloc[-1]
    last_level = float(last.get('target_level_max', 0.0))

    median = last_level
    lower = median - 0.5
    upper = median + 0.5
    prob = 1.0 if median >= 30.0 else 0.0

    result = {
        'timestamp': datetime.now().isoformat(),
        'lead_time_days': lead_time,
        'current_conditions': {
            'date': str(last['date']),
            'current_level_st_louis': round(last_level, 2)
        },
        'forecast': {
            'median': round(median, 2),
            'xgboost': None,
            'bayesian': None,
            'lstm': None,
        },
        'prediction_interval_80pct': {
            'lower': round(lower, 2),
            'upper': round(upper, 2),
            'width': round(upper - lower, 2),
        },
        'conformal_interval_80pct': None,
        'flood_risk': {
            'probability': round(prob, 3),
            'threshold_ft': 30.0,
            'risk_level': 'HIGH' if prob >= 0.7 else ('MODERATE' if prob >= 0.3 else 'LOW'),
            'risk_indicator': '🔴' if prob >= 0.7 else ('🟡' if prob >= 0.3 else '🟢')
        }
    }

    return result


def predict_next_days(raw_data: pd.DataFrame, lead_times: List[int] = [1, 2, 3]) -> List[Dict[str, Any]]:
    """
    Generate predictions for multiple lead times
    
    Args:
        raw_data: DataFrame with 30 days of historical data
        lead_times: List of lead times in days (e.g., [1, 2, 3])
    
    Returns:
        List of prediction dictionaries, each containing:
        - lead_time_days: How many days ahead
        - forecast_date: The date being predicted
        - forecast: Model predictions
        - conformal_interval_80pct: Uncertainty intervals
        - flood_risk: Risk assessment
    """
    
    predictions = []
    
    # Get base date (last date in raw data)
    base_date = pd.to_datetime(raw_data['date'].iloc[-1])
    
    for lead_time in lead_times:
        try:
            logger.info(f"Generating {lead_time}-day prediction...")
            # Calculate forecast date
            forecast_date = base_date + timedelta(days=lead_time)

            # Check cache first
            cached = get_prediction(forecast_date.strftime('%Y-%m-%d'), lead_time)
            if cached is not None:
                logger.info(f"Using cached prediction for {forecast_date.date()} (days_ahead={lead_time})")

                # Derive risk level from cached probability
                prob = cached.get('flood_probability')
                if prob is None:
                    risk_level = None
                    risk_color = None
                else:
                    if prob >= 0.7:
                        risk_level = "HIGH"
                        risk_color = "🔴"
                    elif prob >= 0.3:
                        risk_level = "MODERATE"
                        risk_color = "🟡"
                    else:
                        risk_level = "LOW"
                        risk_color = "🟢"

                prediction = {
                    'lead_time_days': lead_time,
                    'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                    'forecast': {
                        'median': round(cached['predicted_level'], 2) if cached['predicted_level'] is not None else None,
                        'xgboost': None,
                        'bayesian': None,
                        'lstm': None,
                    },
                    'prediction_interval_80pct': None,
                    'conformal_interval_80pct': None,
                    'flood_risk': {
                        'probability': round(cached['flood_probability'], 3) if cached['flood_probability'] is not None else None,
                        'threshold_ft': 30.0,
                        'risk_level': risk_level,
                        'risk_indicator': risk_color,
                    },
                    'cached': True,
                    'cached_at': str(cached.get('created_at'))
                }

                predictions.append(prediction)
                logger.info(f"✓ Used cache for {lead_time}-day prediction: {prediction['forecast']['median']} ft")
                continue

            missing = _missing_model_files(lead_time)
            if missing:
                message = (
                    f"Model files not found for L{lead_time}d. "
                    f"Missing: {', '.join(missing)}. "
                    "Ensure models are present under UI/backend/models/"
                    f"L{lead_time}d/models."
                )
                logger.error(message)
                predictions.append({
                    'lead_time_days': lead_time,
                    'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                    'error': message,
                    'forecast': None,
                    'flood_risk': None
                })
                continue

            # Initialize predictor for this lead time (models guaranteed to exist)
            predictor = FloodPredictorV2(
                lead_time_days=lead_time,
                model_dir=str(_model_dir_for_lead(lead_time))
            )

            # Generate prediction
            result = predictor.predict_from_raw_data(raw_data)
            
            # Package result with lead time and forecast date
            prediction = {
                'lead_time_days': lead_time,
                'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                'forecast': result['forecast'],
                'prediction_interval_80pct': result['prediction_interval_80pct'],
                'conformal_interval_80pct': result['conformal_interval_80pct'],
                'flood_risk': result['flood_risk']
            }
            
            predictions.append(prediction)
            
            logger.info(f"✓ {lead_time}-day prediction: {result['forecast']['median']} ft")
            
            # Save to cache (database) - store median forecast and flood probability
            try:
                insert_prediction(forecast_date.strftime('%Y-%m-%d'), float(result['forecast']['median']), float(result['flood_risk']['probability']), days_ahead=lead_time)
            except Exception as e:
                logger.warning(f"Failed to cache prediction for {forecast_date}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to generate {lead_time}-day prediction: {e}")
            # Continue with other lead times even if one fails
            predictions.append({
                'lead_time_days': lead_time,
                'forecast_date': (base_date + timedelta(days=lead_time)).strftime('%Y-%m-%d'),
                'error': str(e),
                'forecast': None,
                'flood_risk': None
            })
    
    return predictions

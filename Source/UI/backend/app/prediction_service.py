"""
Prediction service - integrates FloodPredictorV2 with database/API
"""
import sys
import os
import pandas as pd
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import logging
from pathlib import Path

from .prediction.inference_api import FloodPredictorV2
from .db import insert_prediction, get_prediction
from .schemas import (
    Prediction,
    Forecast,
    PredictionInterval,
    FloodRisk,
    CurrentConditions,
)
from .db_models import (
    PredictionInsert,
    PredictionDAO,
)

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


def _create_flood_risk(probability: float, threshold: float = 30.0) -> FloodRisk:
    """Create a FloodRisk model from probability."""
    return FloodRisk(
        probability=round(probability, 3),
        threshold_ft=threshold
    )


def _create_current_conditions(last_row: pd.Series) -> CurrentConditions:
    """Create a CurrentConditions model from the last data row."""
    return CurrentConditions(
        date=str(last_row['date']),
        current_level_st_louis=round(float(last_row.get('target_level_max', 0.0)), 2)
    )


def _create_prediction_from_dict(pred_dict: Dict[str, Any]) -> Prediction:
    """Convert a prediction dictionary to a Pydantic Prediction model."""
    # Extract sub-components if present
    forecast = None
    if pred_dict.get('forecast'):
        forecast = Forecast(**pred_dict['forecast'])

    pred_interval = None
    if pred_dict.get('prediction_interval_80pct'):
        pred_interval = PredictionInterval(**pred_dict['prediction_interval_80pct'])

    conformal_interval = None
    if pred_dict.get('conformal_interval_80pct'):
        conformal_interval = PredictionInterval(**pred_dict['conformal_interval_80pct'])

    flood_risk = None
    if pred_dict.get('flood_risk'):
        flood_risk = FloodRisk(**pred_dict['flood_risk'])

    current_conditions = None
    if pred_dict.get('current_conditions'):
        current_conditions = CurrentConditions(**pred_dict['current_conditions'])

    return Prediction(
        lead_time_days=pred_dict['lead_time_days'],
        forecast_date=pred_dict['forecast_date'],
        current_conditions=current_conditions,
        forecast=forecast,
        prediction_interval_80pct=pred_interval,
        conformal_interval_80pct=conformal_interval,
        flood_risk=flood_risk,
        cached=pred_dict.get('cached', False),
        cached_at=pred_dict.get('cached_at'),
        intervals_enriched=pred_dict.get('intervals_enriched'),
        intervals_enrichment_reason=pred_dict.get('intervals_enrichment_reason'),
        error=pred_dict.get('error'),
        base_date=pred_dict.get('base_date'),
        window_start=pred_dict.get('window_start')
    )


def _naive_fallback_prediction(raw_data: pd.DataFrame, lead_time: int) -> Dict[str, Any]:
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

    # Create typed components
    current_conditions = _create_current_conditions(last)
    flood_risk = _create_flood_risk(prob)
    forecast = Forecast(median=round(median, 2))

    prediction_interval = PredictionInterval(
        lower=round(lower, 2),
        upper=round(upper, 2),
        width=round(upper - lower, 2)
    )

    # Convert to dict for compatibility with existing code
    result = {
        'timestamp': datetime.now().isoformat(),
        'lead_time_days': lead_time,
        'current_conditions': current_conditions.model_dump(),
        'forecast': forecast.model_dump(),
        'prediction_interval_80pct': prediction_interval.model_dump(),
        'conformal_interval_80pct': None,
        'flood_risk': flood_risk.model_dump()
    }

    return result


def predict_next_days(raw_data: pd.DataFrame, lead_times: List[int] = [1, 2, 3]) -> List[Prediction]:
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
                # Try to include full intervals when possible. The DB cache only
                # stores median and probability; compute intervals from models
                # if the model files are available. If not available, include a
                # small naive interval around the cached median so the API
                # response remains consistent with the non-cached flow.
                try:
                    missing = _missing_model_files(lead_time)
                    if not missing:
                        predictor = FloodPredictorV2(
                            lead_time_days=lead_time,
                            model_dir=str(_model_dir_for_lead(lead_time))
                        )
                        # Compute full result (intervals, model breakdown)
                        result = predictor.predict_from_raw_data(raw_data)

                        # Prefer model-produced forecast but retain cached median/prob
                        forecast = result.get('forecast', {})
                        if cached.get('predicted_level') is not None:
                            forecast['median'] = round(cached['predicted_level'], 2)

                        prediction = {
                            'lead_time_days': lead_time,
                            'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                            'forecast': forecast,
                            'prediction_interval_80pct': result.get('prediction_interval_80pct'),
                            'conformal_interval_80pct': result.get('conformal_interval_80pct'),
                            'flood_risk': {
                                'probability': round(cached['flood_probability'], 3) if cached['flood_probability'] is not None else result.get('flood_risk', {}).get('probability'),
                                'threshold_ft': 30.0,
                                'risk_level': risk_level,
                                'risk_indicator': risk_color,
                            },
                            'cached': True,
                            'cached_at': str(cached.get('created_at'))
                        }

                        predictions.append(prediction)
                        logger.info(f"✓ Used cache+models for {lead_time}-day prediction: {prediction['forecast']['median']} ft")
                        continue
                    else:
                        # No model files: do NOT fabricate intervals. If the
                        # cached record already contains interval bounds, return
                        # them and mark as enriched-from-cache. Otherwise signal
                        # that intervals are not enriched due to missing models.
                        lower = cached.get('lower_bound_80')
                        upper = cached.get('upper_bound_80')
                        if lower is not None and upper is not None:
                            pi = {'lower': round(float(lower), 2), 'upper': round(float(upper), 2), 'width': round(float(upper) - float(lower), 2)}
                            intervals_enriched = True
                            intervals_reason = 'cached'
                        else:
                            pi = None
                            intervals_enriched = False
                            intervals_reason = 'models_missing'

                        prediction = {
                            'lead_time_days': lead_time,
                            'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                            'forecast': {
                                'median': round(cached['predicted_level'], 2) if cached['predicted_level'] is not None else None,
                                'xgboost': None,
                                'bayesian': None,
                                'lstm': None,
                            },
                            'prediction_interval_80pct': pi,
                            'conformal_interval_80pct': None,
                            'intervals_enriched': intervals_enriched,
                            'intervals_enrichment_reason': intervals_reason,
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
                        logger.info(f"✓ Used cache (no models) for {lead_time}-day prediction: {prediction['forecast']['median']} ft")
                        continue
                except Exception as e:
                    logger.warning(f"Failed to enrich cached prediction with intervals: {e}")
                    # Do not fabricate intervals - surface enrichment failure.
                    lower = cached.get('lower_bound_80')
                    upper = cached.get('upper_bound_80')
                    if lower is not None and upper is not None:
                        pi = {'lower': round(float(lower), 2), 'upper': round(float(upper), 2), 'width': round(float(upper) - float(lower), 2)}
                        intervals_enriched = True
                        intervals_reason = 'cached'
                    else:
                        pi = None
                        intervals_enriched = False
                        intervals_reason = f'enrichment_failed: {str(e)}'

                    prediction = {
                        'lead_time_days': lead_time,
                        'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                        'forecast': {
                            'median': round(cached['predicted_level'], 2) if cached['predicted_level'] is not None else None,
                            'xgboost': None,
                            'bayesian': None,
                            'lstm': None,
                        },
                        'prediction_interval_80pct': pi,
                        'conformal_interval_80pct': None,
                        'intervals_enriched': intervals_enriched,
                        'intervals_enrichment_reason': intervals_reason,
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
                    logger.info(f"✓ Used cache (enrichment failed) for {lead_time}-day prediction: {prediction['forecast']['median']} ft")
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
                pi = result.get('prediction_interval_80pct') or {}
                lower = pi.get('lower') if isinstance(pi, dict) else None
                upper = pi.get('upper') if isinstance(pi, dict) else None

                insert_prediction(
                    forecast_date.strftime('%Y-%m-%d'),
                    float(result['forecast']['median']),
                    float(result['flood_risk']['probability']),
                    days_ahead=lead_time,
                    lower_bound_80=lower,
                    upper_bound_80=upper,
                    model_version=None,
                    model_type=None,
                )
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
    
    # Convert all predictions to Pydantic models
    typed_predictions = [_create_prediction_from_dict(pred) for pred in predictions]
    return typed_predictions


from typing import Callable, Optional


def predict_all_historical(lead_times: List[int] = [1, 2, 3], skip_cached: bool = True,
                            on_progress: Optional[Callable[[dict], None]] = None,
                            cancel_check: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
    """
    Generate predictions for all available historical data points

    This function iterates through all historical data in the database and generates
    predictions for each valid 30-day window, providing a comprehensive backtest
    of the prediction models.

    Args:
        lead_times: List of lead times in days (e.g., [1, 2, 3])
        skip_cached: If True, skip dates that already have predictions cached

    Returns:
        Dictionary with:
        - total_predictions: Total number of predictions generated
        - lead_times: Lead times processed
        - predictions_by_lead_time: Predictions grouped by lead time
        - skipped_cached: Number of predictions skipped due to caching
        - errors: List of errors encountered
        - summary: Summary statistics
    """

    from .db import get_all_raw_data, get_prediction
    import numpy as np

    logger.info(f"Starting historical prediction for all data (lead_times={lead_times}, skip_cached={skip_cached})")

    # Get all historical data
    all_data = get_all_raw_data()
    if all_data is None or len(all_data) < 30:
        error_msg = f"Insufficient historical data: need at least 30 days, got {len(all_data) if all_data is not None else 0}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "total_predictions": 0,
            "lead_times": lead_times,
            "predictions_by_lead_time": {},
            "skipped_cached": 0,
            "errors": [error_msg]
        }

    logger.info(f"Processing {len(all_data)} days of historical data")

    # Initialize results structure
    results = {
        "total_predictions": 0,
        "lead_times": lead_times,
        "predictions_by_lead_time": {lead: [] for lead in lead_times},
        "skipped_cached": 0,
        "errors": [],
        "summary": {}
    }

    # Process each possible 30-day window
    # Start from index 29 (0-based, so 30 days of data available)
    total_windows = max(0, len(all_data) - 29)
    total_steps = total_windows * max(1, len(lead_times))
    completed_steps = 0
    start_ts = datetime.now()

    def _maybe_report_progress(message: Optional[str] = None):
        if on_progress is None:
            return
        elapsed = (datetime.now() - start_ts).total_seconds()
        percent = (completed_steps / total_steps * 100) if total_steps > 0 else 100
        eta_seconds = None
        if completed_steps > 0 and completed_steps < total_steps:
            rate = elapsed / completed_steps
            eta_seconds = int((total_steps - completed_steps) * rate)
        try:
            on_progress({
                "total": total_steps,
                "completed": completed_steps,
                "percent": round(percent, 2),
                "eta_seconds": eta_seconds,
                "message": message or "Running",
            })
        except Exception:
            # Progress callback should not break job execution
            pass

    _maybe_report_progress("Starting")

    for i in range(29, len(all_data)):
        if cancel_check and cancel_check():
            results['errors'].append('Cancelled by user')
            _maybe_report_progress('Cancelled')
            results['summary']['cancelled'] = True
            return results
        try:
            # Get 30-day window ending at position i
            window_data = all_data.iloc[i-29:i+1].copy()
            base_date = window_data['date'].iloc[-1]

            logger.debug(f"Processing window ending at {base_date.date()} (position {i}/{len(all_data)-1})")

            # Generate predictions for each lead time
            for lead_time in lead_times:
                if cancel_check and cancel_check():
                    results['errors'].append('Cancelled by user')
                    _maybe_report_progress('Cancelled')
                    results['summary']['cancelled'] = True
                    return results
                forecast_date = base_date + pd.Timedelta(days=lead_time)

                # Skip if prediction exists and skip_cached is True
                if skip_cached:
                    cached = get_prediction(forecast_date.strftime('%Y-%m-%d'), lead_time)
                    if cached is not None:
                        results["skipped_cached"] += 1
                        completed_steps += 1
                        _maybe_report_progress(f"Skipped cached {forecast_date.date()} +{lead_time}d")
                        continue

                # Generate prediction using existing function
                try:
                    predictions = predict_next_days(window_data, lead_times=[lead_time])
                    if predictions and len(predictions) > 0:
                        pred = predictions[0]
                        # If `predict_next_days` returned a Pydantic model, convert
                        # to a plain dict before mutating keys. This avoids errors
                        # like "'Prediction' object does not support item assignment".
                        if hasattr(pred, "model_dump"):
                            pred = pred.model_dump()

                        pred["base_date"] = base_date.strftime('%Y-%m-%d')
                        pred["window_start"] = window_data['date'].iloc[0].strftime('%Y-%m-%d')
                        results["predictions_by_lead_time"][lead_time].append(pred)
                        results["total_predictions"] += 1
                        completed_steps += 1
                        _maybe_report_progress(f"Generated {lead_time}-day for {forecast_date.date()}: {pred.get('forecast', {}).get('median')}")
                        logger.debug(f"Generated {lead_time}-day prediction for {forecast_date.date()}")
                except Exception as e:
                    error_msg = f"Failed to generate {lead_time}-day prediction for {forecast_date.date()}: {str(e)}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    completed_steps += 1
                    _maybe_report_progress(f"Error for {forecast_date.date()} +{lead_time}d")

        except Exception as e:
            error_msg = f"Failed to process window at position {i}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            continue

    # Generate summary statistics
    for lead_time in lead_times:
        preds = results["predictions_by_lead_time"][lead_time]
        if preds:
            medians = [p.get('forecast', {}).get('median') for p in preds if p.get('forecast', {}).get('median') is not None]
            probabilities = [p.get('flood_risk', {}).get('probability') for p in preds if p.get('flood_risk', {}).get('probability') is not None]

            results["summary"][f"lead_time_{lead_time}"] = {
                "count": len(preds),
                "median_predictions": {
                    "min": min(medians) if medians else None,
                    "max": max(medians) if medians else None,
                    "mean": np.mean(medians) if medians else None,
                    "median": np.median(medians) if medians else None
                },
                "flood_probabilities": {
                    "min": min(probabilities) if probabilities else None,
                    "max": max(probabilities) if probabilities else None,
                    "mean": np.mean(probabilities) if probabilities else None,
                    "median": np.median(probabilities) if probabilities else None
                }
            }

    # Final completion message
    completed_steps = total_steps
    _maybe_report_progress("Completed")
    logger.info(f"Historical prediction complete: {results['total_predictions']} predictions generated, {results['skipped_cached']} skipped due to cache")

    return results

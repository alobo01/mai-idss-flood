"""
Flood Level Prediction - Main predictor class
"""

import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import load_model
from scipy.stats import norm
from scipy.interpolate import interp1d
from datetime import datetime
from pathlib import Path

from .feature_engineer import FeatureEngineer
from .data_fetcher import get_latest_data
from . import config


class FloodPredictor:
    """
    Production inference pipeline for flood level prediction.
    
    Loads pre-trained ensemble models and generates predictions with uncertainty quantification.
    """
    
    def __init__(self, lead_time_days=1, model_dir=None, verbose=True):
        """
        Initialize the flood predictor.
        
        Args:
            lead_time_days: Number of days ahead to forecast (1, 2, or 3)
            model_dir: Custom path to models. If None, uses package models.
            verbose: Print status messages during initialization
        """
        self.lead_time = lead_time_days
        self.verbose = verbose
        self.flood_threshold = config.FLOOD_THRESHOLD_FT
        
        # Set model directory
        if model_dir is None:
            model_dir = config.get_model_path(lead_time_days)
        
        self.model_dir = Path(model_dir)
        
        if self.verbose:
            print(f"Loading models for {lead_time_days}-day forecast...")
        
        # Verify models exist
        if not config.verify_models_exist(lead_time_days):
            raise FileNotFoundError(
                f"Model files not found for {lead_time_days}-day forecast at {self.model_dir}"
            )
        
        self._load_models()
        self._load_calibration()
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer(lead_time_days=lead_time_days)
    
    def _load_models(self):
        """Load all trained models"""
        
        # XGBoost
        self.xgb_q10 = self._load_xgb_regressor(self.model_dir / "xgb_q10.json")
        self.xgb_q50 = self._load_xgb_regressor(self.model_dir / "xgb_q50.json")
        self.xgb_q90 = self._load_xgb_regressor(self.model_dir / "xgb_q90.json")
        
        # Bayesian
        self.bayes_model = joblib.load(self.model_dir / "bayes_model.pkl")
        self.bayes_scaler = joblib.load(self.model_dir / "bayes_scaler.pkl")
        
        # LSTM with custom quantile loss
        def quantile_loss(q):
            def loss(y_true, y_pred):
                e = y_true - y_pred
                return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))
            return loss
        
        self.lstm_q10 = load_model(self.model_dir / "lstm_q10.h5", 
                                   custom_objects={'loss': quantile_loss(0.10)})
        self.lstm_q50 = load_model(self.model_dir / "lstm_q50.h5",
                                   custom_objects={'loss': quantile_loss(0.50)})
        self.lstm_q90 = load_model(self.model_dir / "lstm_q90.h5",
                                   custom_objects={'loss': quantile_loss(0.90)})
        
        self.lstm_scaler_x = joblib.load(self.model_dir / "lstm_scaler_x.pkl")
        self.lstm_scaler_y = joblib.load(self.model_dir / "lstm_scaler_y.pkl")
        
        if self.verbose:
            print("  ✓ All models loaded")

    def _load_xgb_regressor(self, path):
        """Instantiate regressor, ensure estimator type, and load model"""
        model = xgb.XGBRegressor()
        model._estimator_type = "regressor"
        model.load_model(str(path))
        return model
    
    def _load_calibration(self):
        """Load conformal calibration"""
        try:
            calib_path = self.model_dir / "calibration_info.pkl"
            self.calibration = joblib.load(calib_path)
            self.conformal_correction = self.calibration['conformal_correction']
            if self.verbose:
                print(f"  ✓ Conformal correction: {self.conformal_correction:.2f} ft")
        except Exception as e:
            if self.verbose:
                print(f"  ⚠️  No calibration found: {e}")
            self.conformal_correction = 0.0
    
    def _calculate_flood_probability(self, q10, q50, q90, threshold):
        """Estimate P(level > threshold) using quantile interpolation"""
        if threshold <= q10:
            return 0.95
        elif threshold >= q90:
            return 0.05
        else:
            quantiles = np.array([0.10, 0.50, 0.90])
            levels = np.array([q10, q50, q90])
            interp_func = interp1d(levels, quantiles, kind='linear', fill_value='extrapolate')
            prob_below = float(interp_func(threshold))
            return 1.0 - np.clip(prob_below, 0.0, 1.0)
    
    def predict_live(self):
        """
        Fetch live data from APIs and generate prediction.
        
        Returns:
            dict with predictions, intervals, and risk assessment
        """
        
        if self.verbose:
            print("\n" + "="*70)
            print("FETCHING LIVE DATA FROM APIS")
            print("="*70)
        
        # Fetch latest 30 days
        raw_data = get_latest_data()
        
        if self.verbose:
            print("\n" + "="*70)
            print("GENERATING PREDICTION")
            print("="*70)
        
        # Generate prediction
        return self.predict_from_raw_data(raw_data)
    
    def predict_from_raw_data(self, raw_data):
        """
        Generate prediction from raw time series data.
        
        Args:
            raw_data: DataFrame or path to CSV with required columns:
                - date
                - target_level_max
                - hermann_level
                - grafton_level
                - daily_precip
                - daily_temp_avg
                - daily_snowfall
                - daily_humidity
                - daily_wind
                - soil_deep_30d
        
        Returns:
            dict with predictions, intervals, and risk assessment
        """
        
        # Load data
        if isinstance(raw_data, str):
            df = pd.read_csv(raw_data)
        else:
            df = raw_data.copy()
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Create features
        if self.verbose:
            print("  Creating features from raw data...")
        X = self.feature_engineer.create_features(df)
        
        if self.verbose:
            print(f"  Generated {len(X.columns)} features")
        
        # Make predictions
        return self._predict_from_features(X, df)
    
    def _predict_from_features(self, X, raw_data=None):
        """Internal method to predict from engineered features"""
        
        # XGBoost predictions
        xgb_q10 = float(self.xgb_q10.predict(X)[0])
        xgb_q50 = float(self.xgb_q50.predict(X)[0])
        xgb_q90 = float(self.xgb_q90.predict(X)[0])
        
        # Bayesian predictions with uncertainty
        x_bayes = self.bayes_scaler.transform(X)
        mu, sigma = self.bayes_model.predict(x_bayes, return_std=True)
        bayes_q10 = float(mu[0] + norm.ppf(0.10) * sigma[0])
        bayes_q50 = float(mu[0])
        bayes_q90 = float(mu[0] + norm.ppf(0.90) * sigma[0])
        
        # LSTM predictions
        x_lstm = self.lstm_scaler_x.transform(X)
        x_lstm = x_lstm.reshape((1, 1, x_lstm.shape[1]))
        
        lstm_q10 = float(self.lstm_scaler_y.inverse_transform(
            self.lstm_q10.predict(x_lstm, verbose=0))[0, 0])
        lstm_q50 = float(self.lstm_scaler_y.inverse_transform(
            self.lstm_q50.predict(x_lstm, verbose=0))[0, 0])
        lstm_q90 = float(self.lstm_scaler_y.inverse_transform(
            self.lstm_q90.predict(x_lstm, verbose=0))[0, 0])
        
        # Ensemble: combine quantiles
        ensemble_q10 = float(np.min([xgb_q10, bayes_q10, lstm_q10]))
        ensemble_q50 = float(np.median([xgb_q50, bayes_q50, lstm_q50]))
        ensemble_q90 = float(np.max([xgb_q90, bayes_q90, lstm_q90]))
        
        # Conformal calibration
        conformal_lower = ensemble_q10 - self.conformal_correction
        conformal_median = ensemble_q50
        conformal_upper = ensemble_q90 + self.conformal_correction
        
        # Flood probability
        flood_prob = self._calculate_flood_probability(
            ensemble_q10, ensemble_q50, ensemble_q90, self.flood_threshold
        )
        
        # Risk level assessment
        if flood_prob >= config.RISK_THRESHOLDS['MODERATE']:
            risk_level = "HIGH"
            risk_color = config.RISK_COLORS['HIGH']
        elif flood_prob >= config.RISK_THRESHOLDS['LOW']:
            risk_level = "MODERATE"
            risk_color = config.RISK_COLORS['MODERATE']
        else:
            risk_level = "LOW"
            risk_color = config.RISK_COLORS['LOW']
        
        # Get current conditions (if raw data provided)
        current_conditions = {}
        if raw_data is not None and len(raw_data) > 0:
            latest = raw_data.iloc[-1]
            current_conditions = {
                'date': str(latest['date']),
                'current_level_st_louis': round(float(latest['target_level_max']), 2),
                'current_level_hermann': round(float(latest['hermann_level']), 2),
                'current_level_grafton': round(float(latest['grafton_level']), 2),
                'recent_precip_7d': round(float(X['precip_7d'].iloc[0]), 2) if 'precip_7d' in X.columns else None,
            }
        
        # Package results
        result = {
            'timestamp': datetime.now().isoformat(),
            'lead_time_days': self.lead_time,
            
            'current_conditions': current_conditions,
            
            'forecast': {
                'median': round(ensemble_q50, 2),
                'xgboost': round(xgb_q50, 2),
                'bayesian': round(bayes_q50, 2),
                'lstm': round(lstm_q50, 2),
            },
            
            'prediction_interval_80pct': {
                'lower': round(ensemble_q10, 2),
                'upper': round(ensemble_q90, 2),
                'width': round(ensemble_q90 - ensemble_q10, 2),
            },
            
            'conformal_interval_80pct': {
                'lower': round(conformal_lower, 2),
                'median': round(conformal_median, 2),
                'upper': round(conformal_upper, 2),
                'width': round(conformal_upper - conformal_lower, 2),
            },
            
            'flood_risk': {
                'probability': round(flood_prob, 3),
                'threshold_ft': self.flood_threshold,
                'risk_level': risk_level,
                'risk_indicator': risk_color,
            },
        }
        
        return result

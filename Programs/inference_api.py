import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import load_model
from scipy.stats import norm
from scipy.interpolate import interp1d
from datetime import datetime  
from feature_engineer import FeatureEngineer
from data_fetcher import get_latest_data

class FloodPredictorV2:
    """
    Production inference pipeline
    """
    
    def __init__(self, lead_time_days=1, model_dir=None):
        self.lead_time = lead_time_days
        
        if model_dir is None:
            model_dir = f"Results/L{lead_time_days}d/models"
        
        self.model_dir = model_dir
        self.flood_threshold = 30.0
        
        print(f"Loading models for {lead_time_days}-day forecast...")
        self._load_models()
        self._load_calibration()
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer(lead_time_days=lead_time_days)
        
    def _load_models(self):
        """Load all trained models"""
        
        # XGBoost
        self.xgb_q10 = self._load_xgb_regressor(f"{self.model_dir}/xgb_q10.json")
        self.xgb_q50 = self._load_xgb_regressor(f"{self.model_dir}/xgb_q50.json")
        self.xgb_q90 = self._load_xgb_regressor(f"{self.model_dir}/xgb_q90.json")
        
        # Bayesian
        self.bayes_model = joblib.load(f"{self.model_dir}/bayes_model.pkl")
        self.bayes_scaler = joblib.load(f"{self.model_dir}/bayes_scaler.pkl")
        
        # LSTM
        def quantile_loss(q):
            def loss(y_true, y_pred):
                e = y_true - y_pred
                return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))
            return loss
        
        self.lstm_q10 = load_model(f"{self.model_dir}/lstm_q10.h5", 
                                   custom_objects={'loss': quantile_loss(0.10)})
        self.lstm_q50 = load_model(f"{self.model_dir}/lstm_q50.h5",
                                   custom_objects={'loss': quantile_loss(0.50)})
        self.lstm_q90 = load_model(f"{self.model_dir}/lstm_q90.h5",
                                   custom_objects={'loss': quantile_loss(0.90)})
        
        self.lstm_scaler_x = joblib.load(f"{self.model_dir}/lstm_scaler_x.pkl")
        self.lstm_scaler_y = joblib.load(f"{self.model_dir}/lstm_scaler_y.pkl")
        
        print("  ✓ All models loaded")

    def _load_xgb_regressor(self, path):
        """Instantiate regressor, ensure estimator type, and load model"""
        model = xgb.XGBRegressor()
        model._estimator_type = "regressor"
        model.load_model(path)
        return model
    
    def _load_calibration(self):
        """Load conformal calibration"""
        try:
            self.calibration = joblib.load(f"Results/L{self.lead_time}d/calibration_info.pkl")
            self.conformal_correction = self.calibration['conformal_correction']
            print(f"  ✓ Conformal correction: {self.conformal_correction:.2f} ft")
        except:
            print("  ⚠️  No calibration found")
            self.conformal_correction = 0.0
    
    def _calculate_flood_probability(self, q10, q50, q90, threshold):
        """Estimate P(level > threshold)"""
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
        Fetch live data and generate prediction
        
        Returns:
            dict with predictions, intervals, probabilities
        """
        
        print("\n" + "="*70)
        print("FETCHING LIVE DATA FROM APIS")
        print("="*70)
        
        # Fetch latest 30 days
        raw_data = get_latest_data()
        
        print("\n" + "="*70)
        print("GENERATING PREDICTION")
        print("="*70)
        
        # Generate prediction
        return self.predict_from_raw_data(raw_data)
    
    def predict_from_raw_data(self, raw_data):
        """
        Generate prediction from raw time series data
        
        Args:
            raw_data: DataFrame with at least 30 days of data
        
        Returns:
            dict with predictions, intervals, probabilities
        """
        
        # Load data
        if isinstance(raw_data, str):
            df = pd.read_csv(raw_data)
        else:
            df = raw_data.copy()
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Create features
        print("  Creating features from raw data...")
        X = self.feature_engineer.create_features(df)
        
        print(f"  Generated {len(X.columns)} features")
        
        # Make predictions
        return self._predict_from_features(X, df)
    
    def _predict_from_features(self, X, raw_data=None):
        """Internal method to predict from engineered features"""
        
        # XGBoost
        xgb_q10 = float(self.xgb_q10.predict(X)[0])
        xgb_q50 = float(self.xgb_q50.predict(X)[0])
        xgb_q90 = float(self.xgb_q90.predict(X)[0])
        
        # Bayesian
        x_bayes = self.bayes_scaler.transform(X)
        mu, sigma = self.bayes_model.predict(x_bayes, return_std=True)
        bayes_q10 = float(mu[0] + norm.ppf(0.10) * sigma[0])
        bayes_q50 = float(mu[0])
        bayes_q90 = float(mu[0] + norm.ppf(0.90) * sigma[0])
        
        # LSTM
        x_lstm = self.lstm_scaler_x.transform(X)
        x_lstm = x_lstm.reshape((1, 1, x_lstm.shape[1]))
        
        lstm_q10 = float(self.lstm_scaler_y.inverse_transform(
            self.lstm_q10.predict(x_lstm, verbose=0))[0, 0])
        lstm_q50 = float(self.lstm_scaler_y.inverse_transform(
            self.lstm_q50.predict(x_lstm, verbose=0))[0, 0])
        lstm_q90 = float(self.lstm_scaler_y.inverse_transform(
            self.lstm_q90.predict(x_lstm, verbose=0))[0, 0])
        
        # Ensemble
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
        
        # Risk level
        if flood_prob >= 0.7:
            risk_level = "HIGH"
            risk_color = "🔴"
        elif flood_prob >= 0.3:
            risk_level = "MODERATE"
            risk_color = "🟡"
        else:
            risk_level = "LOW"
            risk_color = "🟢"
        
        # Get current conditions (if raw data provided)
        current_conditions = {}
        if raw_data is not None and len(raw_data) > 0:
            latest = raw_data.iloc[-1]
            current_conditions = {
                'date': str(latest['date']),
                'current_level_st_louis': round(float(latest['target_level_max']), 2),
                'current_level_hermann': round(float(latest['hermann_level']), 2),
                'current_level_grafton': round(float(latest['grafton_level']), 2),
                'recent_precip_7d': round(float(X['precip_7d'].iloc[0]), 2),
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

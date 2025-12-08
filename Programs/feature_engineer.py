"""
Feature Engineering Module - Auto-detects feature order from training data
"""
import pandas as pd
import numpy as np
import os

class FeatureEngineer:
    """
    Automatically creates all lag features and moving averages
    """
    
    def __init__(self, lead_time_days=1):
        self.lead_time = lead_time_days
        
        # Load feature order from actual training data
        self._load_feature_order()
    
    def _load_feature_order(self):
        """Load exact feature order from training CSV"""
        
        train_file = f"Data/processed/L{self.lead_time}d/train.csv"
        
        if not os.path.exists(train_file):
            raise FileNotFoundError(
                f"Training data not found: {train_file}\n"
                f"Please train models for {self.lead_time}-day forecast first."
            )
        
        # Load just the header
        df = pd.read_csv(train_file, nrows=0)
        
        # Exclude target and metadata columns
        EXCLUDE = ['date', 'time', 'target_level_max', 'target_level_mean',
                  'target_level_min', 'target_level_std', 'target_level',
                  'is_flood', 'is_major_flood', 'flood_probability',
                  'ensemble_q10', 'ensemble_q50', 'ensemble_q90',
                  'conformal_lower', 'conformal_median', 'conformal_upper']
        
        self.feature_order = [c for c in df.columns if c not in EXCLUDE]
        
        print(f"  Loaded {len(self.feature_order)} features from training data")
    
    def create_features(self, df):
        """
        Create all required features from raw data
        
        Args:
            df: DataFrame with columns:
                - date (datetime)
                - target_level_max (St. Louis river level)
                - hermann_level (upstream station)
                - grafton_level (upstream station)
                - daily_precip (mm)
                - daily_temp_avg (°C)
                - daily_snowfall (mm)
                - daily_humidity (%)
                - daily_wind (m/s)
                - soil_deep_30d (moisture 28-100cm)
        
        Returns:
            DataFrame with one row containing all features in correct order
        """
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Need at least 30 days
        if len(df) < 30:
            raise ValueError(f"Need at least 30 days of data, got {len(df)}")
        
        # Get most recent date (the one we're predicting FROM)
        latest_idx = len(df) - 1
        
        features = {}
        
        # =====================================================================
        # STEP 1: GENERATE ALL POSSIBLE FEATURES
        # =====================================================================
        
        # Current station levels
        features['grafton_level'] = df.loc[latest_idx, 'grafton_level']
        features['hermann_level'] = df.loc[latest_idx, 'hermann_level']
        
        # Current weather
        features['daily_precip'] = df.loc[latest_idx, 'daily_precip']
        features['daily_temp_avg'] = df.loc[latest_idx, 'daily_temp_avg']
        features['daily_snowfall'] = df.loc[latest_idx, 'daily_snowfall']
        features['daily_humidity'] = df.loc[latest_idx, 'daily_humidity']
        features['daily_wind'] = df.loc[latest_idx, 'daily_wind']
        
        # Precipitation windows
        features['precip_7d'] = df.loc[max(0, latest_idx-6):latest_idx+1, 'daily_precip'].sum()
        features['precip_14d'] = df.loc[max(0, latest_idx-13):latest_idx+1, 'daily_precip'].sum()
        features['precip_30d'] = df.loc[max(0, latest_idx-29):latest_idx+1, 'daily_precip'].sum()
        
        # Soil moisture
        features['soil_deep_30d'] = df.loc[max(0, latest_idx-29):latest_idx+1, 'soil_deep_30d'].mean()
        
        # Heavy rain indicator
        if latest_idx >= 1:
            precip_48h = df.loc[latest_idx-1:latest_idx+1, 'daily_precip'].sum()
        else:
            precip_48h = df.loc[latest_idx, 'daily_precip']
        features['heavy_rain_48h'] = 1 if precip_48h > 15 else 0
        
        # Generate ALL possible lag features (up to 10 days to cover 2-day and 3-day models)
        for lag in range(1, 11):
            lag_idx = latest_idx - lag
            
            if lag_idx >= 0:
                # Station lags
                features[f'hermann_lag{lag}d'] = df.loc[lag_idx, 'hermann_level']
                features[f'grafton_lag{lag}d'] = df.loc[lag_idx, 'grafton_level']
                features[f'target_lag{lag}d'] = df.loc[lag_idx, 'target_level_max']
                
                # Weather lags
                features[f'daily_precip_lag{lag}d'] = df.loc[lag_idx, 'daily_precip']
                
                # Precipitation window lags
                start_7d = max(0, lag_idx - 6)
                start_14d = max(0, lag_idx - 13)
                start_30d = max(0, lag_idx - 29)
                
                features[f'precip_7d_lag{lag}d'] = df.loc[start_7d:lag_idx+1, 'daily_precip'].sum()
                features[f'precip_14d_lag{lag}d'] = df.loc[start_14d:lag_idx+1, 'daily_precip'].sum()
                features[f'precip_30d_lag{lag}d'] = df.loc[start_30d:lag_idx+1, 'daily_precip'].sum()
                features[f'soil_deep_30d_lag{lag}d'] = df.loc[start_30d:lag_idx+1, 'soil_deep_30d'].mean()
            else:
                # Set to NaN if not enough history
                features[f'hermann_lag{lag}d'] = np.nan
                features[f'grafton_lag{lag}d'] = np.nan
                features[f'target_lag{lag}d'] = np.nan
                features[f'daily_precip_lag{lag}d'] = np.nan
                features[f'precip_7d_lag{lag}d'] = np.nan
                features[f'precip_14d_lag{lag}d'] = np.nan
                features[f'precip_30d_lag{lag}d'] = np.nan
                features[f'soil_deep_30d_lag{lag}d'] = np.nan
        
        # Moving averages (3, 7, 14 days)
        for window in [3, 7, 14]:
            start_idx = max(0, latest_idx - window + 1)
            features[f'hermann_ma{window}d'] = df.loc[start_idx:latest_idx+1, 'hermann_level'].mean()
            features[f'grafton_ma{window}d'] = df.loc[start_idx:latest_idx+1, 'grafton_level'].mean()
        
        # =====================================================================
        # STEP 2: FILTER TO ONLY FEATURES NEEDED BY MODEL (in correct order)
        # =====================================================================
        
        ordered_features = {}
        missing_features = []
        
        for col in self.feature_order:
            if col in features:
                ordered_features[col] = features[col]
            else:
                ordered_features[col] = np.nan
                missing_features.append(col)
        
        if missing_features:
            print(f"  ⚠️  Warning: Could not compute these features (set to NaN): {missing_features}")
        
        # Convert to DataFrame with correct column order
        result = pd.DataFrame([ordered_features])
        
        # Verify column order matches exactly
        if list(result.columns) != self.feature_order:
            raise ValueError("Feature order mismatch after creation!")
        
        return result
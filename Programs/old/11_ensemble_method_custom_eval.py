import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error
import os

print("=" * 70)
print("FAST ENSEMBLE: LOADING PRE-TRAINED ARTIFACTS")
print("=" * 70)

# =============================================================================
# 1. LOAD DATA (SHARED)
# =============================================================================
# Always use the same dataset logic
if os.path.exists("Data/processed/daily_flood_dataset_48h_lags.csv"):
    val_df = pd.read_csv("Data/processed/daily_val.csv")
    print("  ✓ Loaded 48h Validation Data")
else:
    val_df = pd.read_csv("Data/processed/daily_val.csv")
    print("  ✓ Loaded Standard Validation Data")

# Define features (must match exactly what models were trained on)
EXCLUDE_FEATURES = [
    'date', 'time', 'target_level_max', 'target_level_mean',
    'target_level_min', 'target_level_std', 'target_level',
    'is_flood', 'is_major_flood', 'hermann_level', 'grafton_level'
]
feature_cols = [c for c in val_df.columns if c not in EXCLUDE_FEATURES]

X_val = val_df[feature_cols].fillna(0)
y_val = val_df['target_level_max'].fillna(0)

# =============================================================================
# 2. LOAD MODEL ARTIFACTS
# =============================================================================
print("\n2. Loading Pre-Trained Models...")

# A. Load XGBoost
xgb_model = xgb.XGBRegressor()
xgb_model.load_model("Results/models/xgb_q90.json")
pred_xgb = xgb_model.predict(X_val)
print("  ✓ Loaded XGBoost (q90)")

# B. Load Bayesian
bayes_model = joblib.load("Results/models/bayesian_model.pkl")
pred_bayes_mean, pred_bayes_std = bayes_model.predict(X_val, return_std=True)
pred_bayes = pred_bayes_mean + pred_bayes_std  # Safety Bound
print("  ✓ Loaded Bayesian Ridge")


# C. Load LSTM & Scalers
# We need to re-define the custom loss to load the model
def quantile_loss(q, y_true, y_pred):
    e = y_true - y_pred
    return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))


# Load Scalers
scaler_X = joblib.load("Results/models/lstm_scaler_X.pkl")
scaler_y = joblib.load("Results/models/lstm_scaler_y.pkl")

# Prepare Data for LSTM (Scaling)
X_val_scaled = scaler_X.transform(X_val)
X_val_lstm = X_val_scaled.reshape((X_val_scaled.shape[0], 1, X_val_scaled.shape[1]))

# Load Model
lstm_model = load_model("Results/models/lstm_q90.h5",
                        custom_objects={'safety_loss': lambda y, p: quantile_loss(0.90, y, p)})
pred_lstm_scaled = lstm_model.predict(X_val_lstm, verbose=0)
pred_lstm = scaler_y.inverse_transform(pred_lstm_scaled).flatten()
print("  ✓ Loaded LSTM & Scalers")

# =============================================================================
# 3. CREATE ENSEMBLE (SAFETY MAX)
# =============================================================================
print("\n3. Running Safety Max Ensemble...")

# The "Paranoid" Strategy: Take the highest prediction
ensemble_max = np.maximum(pred_xgb, np.maximum(pred_lstm, pred_bayes))

# =============================================================================
# 4. EVALUATION
# =============================================================================
FLOOD_THRESHOLD = 30.0


def quick_score(y_true, y_pred, name):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    is_flood = y_true >= FLOOD_THRESHOLD
    is_pred_flood = y_pred >= FLOOD_THRESHOLD

    missed = (is_flood & ~is_pred_flood).sum()
    false_alarms = (~is_flood & is_pred_flood).sum()

    print(f"\nResults for {name}:")
    print(f"  - Missed Floods: {missed} {'✅' if missed == 0 else '❌'}")
    print(f"  - False Alarms:  {false_alarms}")
    print(f"  - RMSE:          {np.sqrt(mean_squared_error(y_true, y_pred)):.2f}")


quick_score(y_val, ensemble_max, "Safety Max Ensemble")
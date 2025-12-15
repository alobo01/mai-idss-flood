import pandas as pd
import numpy as np
import argparse
import os
import joblib
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Config
tf.random.set_seed(42)
np.random.seed(42)

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
args = parser.parse_args()

LEAD_TIME = args.days
DATA_DIR = f"Data/processed/L{LEAD_TIME}d"
MODEL_DIR = f"./Results/L{LEAD_TIME}d/models"

print("=" * 70)
print(f"STEP 06: TRAINING ALL MODELS (L{LEAD_TIME}d)")
print("=" * 70)

os.makedirs(MODEL_DIR, exist_ok=True)

# 1. LOAD DATA
train = pd.read_csv(f"{DATA_DIR}/train.csv")
val = pd.read_csv(f"{DATA_DIR}/val.csv")

# Identify Features
EXCLUDE = ['date', 'time', 'target_level_max', 'target_level_mean',
           'target_level_min', 'target_level_std', 'target_level',
           'is_flood', 'is_major_flood']
features = [c for c in train.columns if c not in EXCLUDE]
target = 'target_level_max'

X_train, y_train = train[features], train[target]
X_val, y_val = val[features], val[target]

print(f"  Features: {len(features)}")

# =============================================================================
# A. XGBOOST (Safety Quantile q90)
# =============================================================================
print("\n[A] Training XGBoost (q90)...")
xgb_model = xgb.XGBRegressor(
    objective='reg:quantileerror',
    quantile_alpha=0.90,
    n_estimators=300, max_depth=4, learning_rate=0.05, n_jobs=-1
)
xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
xgb_model.save_model(f"{MODEL_DIR}/xgb_q90.json")
print("  ✓ Saved XGBoost")

# =============================================================================
# B. BAYESIAN RIDGE (Probabilistic)
# =============================================================================
print("\n[B] Training Bayesian Ridge...")
# Scale features for Bayesian Ridge (Important!)
bayes_scaler = StandardScaler()
X_train_bayes = bayes_scaler.fit_transform(X_train)

bayes_model = BayesianRidge()
bayes_model.fit(X_train_bayes, y_train)

joblib.dump(bayes_model, f"{MODEL_DIR}/bayes_model.pkl")
joblib.dump(bayes_scaler, f"{MODEL_DIR}/bayes_scaler.pkl")
print("  ✓ Saved Bayesian")

# =============================================================================
# C. LSTM (Deep Learning)
# =============================================================================
print("\n[C] Training LSTM...")
# Scale for LSTM
scaler_x = MinMaxScaler()
scaler_y = MinMaxScaler()

X_train_sc = scaler_x.fit_transform(X_train)
X_val_sc = scaler_x.transform(X_val)
y_train_sc = scaler_y.fit_transform(y_train.values.reshape(-1,1))
y_val_sc = scaler_y.transform(y_val.values.reshape(-1,1))

# Reshape (N, 1, Features)
X_train_lstm = X_train_sc.reshape((X_train_sc.shape[0], 1, X_train_sc.shape[1]))
X_val_lstm = X_val_sc.reshape((X_val_sc.shape[0], 1, X_val_sc.shape[1]))

# Custom Loss
def quantile_loss(q, y_true, y_pred):
    e = y_true - y_pred
    return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))

model = Sequential([
    LSTM(64, input_shape=(1, len(features)), return_sequences=False),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1)
])
model.compile(optimizer='adam', loss=lambda y, p: quantile_loss(0.90, y, p))

early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
model.fit(X_train_lstm, y_train_sc, validation_data=(X_val_lstm, y_val_sc),
          epochs=50, batch_size=32, verbose=0, callbacks=[early_stop])

model.save(f"{MODEL_DIR}/lstm_q90.h5")
joblib.dump(scaler_x, f"{MODEL_DIR}/lstm_scaler_x.pkl")
joblib.dump(scaler_y, f"{MODEL_DIR}/lstm_scaler_y.pkl")
print("  ✓ Saved LSTM")
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
MODEL_DIR = f"./L{LEAD_TIME}d/models"

print("=" * 70)
print(f"STEP 07b: TRAINING QUANTILE MODELS (L{LEAD_TIME}d)")
print("=" * 70)

os.makedirs(MODEL_DIR, exist_ok=True)

# =============================================================================
# 1. LOAD DATA
# =============================================================================

train = pd.read_csv(f"{DATA_DIR}/train.csv")
val = pd.read_csv(f"{DATA_DIR}/val.csv")

EXCLUDE = ['date', 'time', 'target_level_max', 'target_level_mean',
           'target_level_min', 'target_level_std', 'target_level',
           'is_flood', 'is_major_flood']

features = [c for c in train.columns if c not in EXCLUDE]
target = 'target_level_max'

X_train, y_train = train[features], train[target]
X_val, y_val = val[features], val[target]

print(f"  Features: {len(features)}")
print(f"  Training: {len(X_train)} samples")
print(f"  Validation: {len(X_val)} samples")

# =============================================================================
# 2. TRAIN MULTI-QUANTILE MODELS
# =============================================================================

QUANTILES = [0.10, 0.50, 0.90]  # 80% prediction interval

print("\n" + "=" * 70)
print("TRAINING MULTI-QUANTILE MODELS")
print("=" * 70)

# -----------------------------------------------------------------------------
# A. XGBOOST - 3 QUANTILES
# -----------------------------------------------------------------------------

print("\n[A] XGBoost Quantile Models...")

for q in QUANTILES:
    print(f"  Training q={q:.2f}...")

    model = xgb.XGBRegressor(
        objective='reg:quantileerror',
        quantile_alpha=q,
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42
    )

    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    # Save
    q_label = int(q * 100)
    model.save_model(f"{MODEL_DIR}/xgb_q{q_label}.json")

    # Quick validation check
    pred_val = model.predict(X_val)
    coverage = ((y_val >= pred_val) if q < 0.5 else (y_val <= pred_val)).mean()
    print(f"    Val coverage: {coverage:.1%} (target: {q if q < 0.5 else (1 - q):.1%})")

print("  ✓ Saved XGBoost quantiles")

# -----------------------------------------------------------------------------
# B. BAYESIAN - MEAN + MULTIPLE SIGMAS
# -----------------------------------------------------------------------------

print("\n[B] Bayesian Ridge (Probabilistic)...")

# Scale features
bayes_scaler = StandardScaler()
X_train_bayes = bayes_scaler.fit_transform(X_train)
X_val_bayes = bayes_scaler.transform(X_val)

# Train
bayes_model = BayesianRidge(
    max_iter=300,
    alpha_1=1e-6,
    alpha_2=1e-6,
    lambda_1=1e-6,
    lambda_2=1e-6
)
bayes_model.fit(X_train_bayes, y_train)

# Validate prediction intervals
mu_val, sigma_val = bayes_model.predict(X_val_bayes, return_std=True)

# Create quantile predictions using normal distribution assumption
from scipy.stats import norm

quantile_preds = {}
for q in QUANTILES:
    z_score = norm.ppf(q)
    pred_q = mu_val + z_score * sigma_val
    quantile_preds[q] = pred_q

    # Check coverage
    coverage = ((y_val >= pred_q) if q < 0.5 else (y_val <= pred_q)).mean()
    print(f"  q={q:.2f} coverage: {coverage:.1%} (target: {q if q < 0.5 else (1 - q):.1%})")

# Save model and scaler
joblib.dump(bayes_model, f"{MODEL_DIR}/bayes_model.pkl")
joblib.dump(bayes_scaler, f"{MODEL_DIR}/bayes_scaler.pkl")

print("  ✓ Saved Bayesian model")

# -----------------------------------------------------------------------------
# C. LSTM - 3 QUANTILES
# -----------------------------------------------------------------------------

print("\n[C] LSTM Quantile Models...")

# Scale data (same for all quantiles)
scaler_x = MinMaxScaler()
scaler_y = MinMaxScaler()

X_train_sc = scaler_x.fit_transform(X_train)
X_val_sc = scaler_x.transform(X_val)
y_train_sc = scaler_y.fit_transform(y_train.values.reshape(-1, 1))
y_val_sc = scaler_y.transform(y_val.values.reshape(-1, 1))

# Reshape for LSTM
X_train_lstm = X_train_sc.reshape((X_train_sc.shape[0], 1, X_train_sc.shape[1]))
X_val_lstm = X_val_sc.reshape((X_val_sc.shape[0], 1, X_val_sc.shape[1]))


# Quantile loss function
def quantile_loss(q):
    def loss(y_true, y_pred):
        e = y_true - y_pred
        return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))

    return loss


for q in QUANTILES:
    print(f"  Training q={q:.2f}...")

    model = Sequential([
        LSTM(64, input_shape=(1, len(features)), return_sequences=False),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss=quantile_loss(q))

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True,
        verbose=0
    )

    model.fit(
        X_train_lstm, y_train_sc,
        validation_data=(X_val_lstm, y_val_sc),
        epochs=100,
        batch_size=32,
        verbose=0,
        callbacks=[early_stop]
    )

    # Validate
    pred_val_sc = model.predict(X_val_lstm, verbose=0)
    pred_val = scaler_y.inverse_transform(pred_val_sc).flatten()
    coverage = ((y_val >= pred_val) if q < 0.5 else (y_val <= pred_val)).mean()
    print(f"    Val coverage: {coverage:.1%} (target: {q if q < 0.5 else (1 - q):.1%})")

    # Save
    q_label = int(q * 100)
    model.save(f"{MODEL_DIR}/lstm_q{q_label}.h5")

# Save scalers (shared across quantiles)
joblib.dump(scaler_x, f"{MODEL_DIR}/lstm_scaler_x.pkl")
joblib.dump(scaler_y, f"{MODEL_DIR}/lstm_scaler_y.pkl")

print("  ✓ Saved LSTM quantiles")

# =============================================================================
# 3. SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("QUANTILE TRAINING COMPLETE")
print("=" * 70)

print(f"\n📊 Models trained:")
print(f"  - XGBoost: q10, q50, q90")
print(f"  - Bayesian: probabilistic (mean + std)")
print(f"  - LSTM: q10, q50, q90")

print(f"\n💡 Saved to: {MODEL_DIR}/")
print(f"  - *_q10.json/h5 (lower bound)")
print(f"  - *_q50.json/h5 (median)")
print(f"  - *_q90.json/h5 (upper bound)")

print("\n⏭️  Next: Run 08b_add_conformal_intervals.py")
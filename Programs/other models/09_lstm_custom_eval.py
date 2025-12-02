import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import os
import random
import joblib

# Set seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)
random.seed(42)

print("=" * 70)
print("LSTM MODEL WITH SAFETY-QUANTILE LOSS")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0  # Feet
TARGET = 'target_level_max'
QUANTILE = 0.90  # The safety factor (90th percentile)

# Features to exclude (Same as Baseline)
EXCLUDE_FEATURES = [
    'date', 'time', 'target_level_max', 'target_level_mean',
    'target_level_min', 'target_level_std', 'target_level',
    'is_flood', 'is_major_flood', 'hermann_level', 'grafton_level'
]

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("\n1. Loading Data...")
train_df = pd.read_csv("Data/processed/daily_train.csv")
val_df = pd.read_csv("Data/processed/daily_val.csv")

# =============================================================================
# 2. PREPROCESSING (SCALING)
# =============================================================================
print("\n2. Scaling Data (Critical for LSTMs)...")

# Prepare X (Features)
feature_cols = [c for c in train_df.columns if c not in EXCLUDE_FEATURES]
X_train_raw = train_df[feature_cols].values
X_val_raw = val_df[feature_cols].values

# Prepare y (Target)
y_train_raw = train_df[TARGET].values.reshape(-1, 1)
y_val_raw = val_df[TARGET].values.reshape(-1, 1)

# Scalers
scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

# Fit on TRAIN only, transform VAL
X_train_scaled = scaler_X.fit_transform(X_train_raw)
X_val_scaled = scaler_X.transform(X_val_raw)

y_train_scaled = scaler_y.fit_transform(y_train_raw)
y_val_scaled = scaler_y.transform(y_val_raw)

# Reshape for LSTM: (Samples, TimeSteps, Features)
# We treat the existing lag features as a single time step vector
X_train_lstm = X_train_scaled.reshape((X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
X_val_lstm = X_val_scaled.reshape((X_val_scaled.shape[0], 1, X_val_scaled.shape[1]))

print(f"  ✓ Training shape: {X_train_lstm.shape}")
print(f"  ✓ Validation shape: {X_val_lstm.shape}")


# =============================================================================
# 3. DEFINE CUSTOM SAFETY LOSS
# =============================================================================
def quantile_loss(q, y_true, y_pred):
    """
    Custom Loss Function that penalizes underpredictions more than overpredictions.
    q=0.90 means underpredicting is 9x more expensive than overpredicting.
    """
    e = y_true - y_pred
    return tf.reduce_mean(tf.maximum(q * e, (q - 1) * e))


# Wrapper to pass 'q' parameter
def safety_loss(y_true, y_pred):
    return quantile_loss(QUANTILE, y_true, y_pred)


# =============================================================================
# 4. BUILD AND TRAIN LSTM
# =============================================================================
print(f"\n3. Training LSTM (Safety q={QUANTILE})...")

model = Sequential([
    LSTM(64, input_shape=(1, X_train_lstm.shape[2]), return_sequences=False),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1, activation='linear')
])

model.compile(optimizer='adam', loss=safety_loss)

# Early stopping to prevent overfitting
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train_lstm, y_train_scaled,
    validation_data=(X_val_lstm, y_val_scaled),
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

# =============================================================================
# 5. PREDICT AND INVERSE SCALE
# =============================================================================
print("\n4. Generating Predictions...")

# Predict
pred_scaled = model.predict(X_val_lstm)

# Inverse Scale back to feet
y_pred_final = scaler_y.inverse_transform(pred_scaled).flatten()
y_val_final = y_val_raw.flatten()


# =============================================================================
# 6. EVALUATION (SAME AS BASELINE)
# =============================================================================
def calculate_safety_scorecard(y_true, y_pred, threshold=30.0):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    is_flood_actual = y_true >= threshold
    is_flood_pred = y_pred >= threshold

    TP = (is_flood_actual & is_flood_pred).sum()
    FP = (~is_flood_actual & is_flood_pred).sum()
    FN = (is_flood_actual & ~is_flood_pred).sum()

    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    residuals = y_pred - y_true
    mean_bias = np.mean(residuals)

    flood_indices = y_true >= threshold
    flood_rmse = np.sqrt(
        mean_squared_error(y_true[flood_indices], y_pred[flood_indices])) if flood_indices.sum() > 0 else 0.0

    return {
        'Missed Floods (Count)': int(FN),
        'Recall (Safety)': round(recall, 3),
        'Mean Bias (ft)': round(mean_bias, 3),
        'False Alarms (Count)': int(FP),
        'Flood RMSE (ft)': round(flood_rmse, 3),
        'Overall RMSE (ft)': round(np.sqrt(mean_squared_error(y_true, y_pred)), 3)
    }


scores = calculate_safety_scorecard(y_val_final, y_pred_final, FLOOD_THRESHOLD)

# Print Scorecard
print("\n" + "=" * 80)
print("FINAL LSTM SCORECARD")
print("=" * 80)
print(pd.DataFrame([scores], index=['LSTM (q90)']).to_string())
print("=" * 80)

# =============================================================================
# 7. VISUALIZATION
# =============================================================================
print("\n5. Saving Plots...")
os.makedirs("Results/lstm_eval", exist_ok=True)

# Safety Quadrant Plot
plt.figure(figsize=(8, 8))
plt.scatter(y_val_final, y_pred_final, alpha=0.5, c='grey', s=15, label='Normal')

# Highlight Floods
flood_mask = y_val_final >= FLOOD_THRESHOLD
hits = (y_val_final >= FLOOD_THRESHOLD) & (y_pred_final >= FLOOD_THRESHOLD)
misses = (y_val_final >= FLOOD_THRESHOLD) & (y_pred_final < FLOOD_THRESHOLD)
alarms = (y_val_final < FLOOD_THRESHOLD) & (y_pred_final >= FLOOD_THRESHOLD)

plt.scatter(y_val_final[hits], y_pred_final[hits], c='green', s=50, label='Detected', edgecolors='black')
plt.scatter(y_val_final[misses], y_pred_final[misses], c='red', s=80, marker='X', label='Missed', edgecolors='black')
plt.scatter(y_val_final[alarms], y_pred_final[alarms], c='orange', s=30, marker='s', label='False Alarm')

plt.axhline(FLOOD_THRESHOLD, color='black', linestyle='--')
plt.axvline(FLOOD_THRESHOLD, color='black', linestyle='--')
plt.title(f"LSTM (q=0.9) Performance\nMissed: {sum(misses)} | False Alarms: {sum(alarms)}")
plt.xlabel("Actual Level (ft)")
plt.ylabel("Predicted Level (ft)")
plt.grid(True, alpha=0.3)
plt.legend()

# 1:1 line
lims = [0, 45]
plt.plot(lims, lims, 'k-', alpha=0.2, zorder=0)

plt.savefig('Results/lstm_eval/lstm_safety_quadrant.png', dpi=150)
print("  ✓ Saved: Results/lstm_eval/lstm_safety_quadrant.png")

# Save Model (optional)
model.save("Results/models/lstm_q90.h5")

# Save the Scalers so we can use them later!
joblib.dump(scaler_X, "Results/models/lstm_scaler_X.pkl")
joblib.dump(scaler_y, "Results/models/lstm_scaler_y.pkl")
print("  ✓ Saved LSTM Scalers to Results/models/")
print("  ✓ Saved: Results/models/lstm_q90.h5")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import BayesianRidge
from sklearn.metrics import mean_squared_error
import os
import joblib

print("=" * 70)
print("BAYESIAN RIDGE REGRESSION (PROBABILISTIC BASELINE)")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0
TARGET = 'target_level_max'

# Same exclusions to prevent leakage
EXCLUDE_FEATURES = [
    'date', 'time', 'target_level_max', 'target_level_mean',
    'target_level_min', 'target_level_std', 'target_level',
    'is_flood', 'is_major_flood', 'hermann_level', 'grafton_level'
]

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("\n1. Loading Data...")
# We use the 48h dataset if available (for fair comparison with 2-day lead time)
if os.path.exists("Data/processed/daily_flood_dataset_48h_lags.csv"):
    train_df = pd.read_csv("Data/processed/daily_train.csv")  # Note: splits might need regeneration if file changed
    # For simplicity, we assume the standard daily_train.csv is compatible or user regenerates splits
    # If you strictly want 48h, ensure daily_train.csv was generated from 48h source
else:
    train_df = pd.read_csv("Data/processed/daily_train.csv")

val_df = pd.read_csv("Data/processed/daily_val.csv")

# Feature Prep
feature_cols = [c for c in train_df.columns if c not in EXCLUDE_FEATURES]
X_train = train_df[feature_cols].fillna(0)  # BayesianRidge cannot handle NaNs
y_train = train_df[TARGET].fillna(0)
X_val = val_df[feature_cols].fillna(0)
y_val = val_df[TARGET].fillna(0)

# =============================================================================
# 2. TRAIN BAYESIAN MODEL
# =============================================================================
print("\n2. Training Bayesian Ridge...")
# BayesianRidge infers the precision of the noise automatically
model = BayesianRidge(compute_score=True)
model.fit(X_train, y_train)

# =============================================================================
# 3. PREDICT WITH UNCERTAINTY
# =============================================================================
print("\n3. Generating Probabilistic Predictions...")

# return_std=True is the Magic Switch!
# It gives us the standard deviation (uncertainty) for EVERY prediction
y_pred_mean, y_pred_std = model.predict(X_val, return_std=True)

# Create a "Safe" prediction by adding 2 Standard Deviations (approx 95% confidence)
# This is dynamic: if the model is unsure, the buffer grows automatically
y_pred_safe = y_pred_mean + (2.0 * y_pred_std)

print(f"  ✓ Predictions generated")
print(f"  ✓ Average Uncertainty (Std Dev): {y_pred_std.mean():.4f} ft")


# =============================================================================
# 4. EVALUATION
# =============================================================================
def calculate_safety_scorecard(y_true, y_pred_safe, threshold=30.0):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred_safe)

    is_flood_actual = y_true >= threshold
    is_flood_pred = y_pred >= threshold

    TP = (is_flood_actual & is_flood_pred).sum()
    FP = (~is_flood_actual & is_flood_pred).sum()
    FN = (is_flood_actual & ~is_flood_pred).sum()

    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    return {
        'Missed Floods': int(FN),
        'Recall': round(recall, 3),
        'False Alarms': int(FP),
        'Safe Prediction Bias': round(np.mean(y_pred - y_true), 3)
    }


scores = calculate_safety_scorecard(y_val, y_pred_safe, FLOOD_THRESHOLD)

print("\n" + "=" * 80)
print("BAYESIAN SAFETY SCORECARD (Mean + 2*Sigma)")
print("=" * 80)
print(pd.DataFrame([scores], index=['Bayesian Ridge']).to_string())
print("=" * 80)

# =============================================================================
# 5. VISUALIZATION
# =============================================================================
os.makedirs("Results/bayesian_eval", exist_ok=True)

plt.figure(figsize=(12, 6))
# Plot only a slice to see the "Confidence Bounds" clearly
subset_idx = range(100, 200)  # Arbitrary zoom
plt.plot(range(len(subset_idx)), y_val.iloc[subset_idx], 'k-', label='Actual', linewidth=2)
plt.plot(range(len(subset_idx)), y_pred_mean[subset_idx], 'b--', label='Mean Prediction')

# Plot the "Safety Cloud"
plt.fill_between(range(len(subset_idx)),
                 y_pred_mean[subset_idx] - 2 * y_pred_std[subset_idx],
                 y_pred_mean[subset_idx] + 2 * y_pred_std[subset_idx],
                 color='blue', alpha=0.2, label='95% Confidence Interval')

plt.axhline(FLOOD_THRESHOLD, color='r', linestyle=':', label='Flood Stage')
plt.title("Bayesian Prediction with Uncertainty Bounds")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('Results/bayesian_eval/uncertainty_cloud.png', dpi=150)
print("\n  ✓ Saved plot to Results/bayesian_eval/uncertainty_cloud.png")

joblib.dump(model, "Results/models/bayesian_model.pkl")
print("  ✓ Saved Bayesian Artifact: Results/models/bayesian_model.pkl")
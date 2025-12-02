import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import os

print("=" * 70)
print("CUSTOM EVALUATION: SAFETY-FIRST FLOOD METRICS")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0  # Feet
TARGET = 'target_level_max'

# Features to exclude (Data Leakage Prevention)
EXCLUDE_FEATURES = [
    'date', 'time', 'target_level_max', 'target_level_mean',
    'target_level_min', 'target_level_std', 'target_level',
    'is_flood', 'is_major_flood', 'hermann_level', 'grafton_level'
]

# Model Candidates
MODELS_CONFIG = {
    'Baseline (MSE)': {
        'params': {'objective': 'reg:squarederror'},
        'bias_adjustment': 0.0
    },
    'Conservative (+1.5ft)': {
        'params': {'objective': 'reg:squarederror'},
        'bias_adjustment': 1.5  # Add 1.5ft safety buffer
    },
    'Safety Quantile (q90)': {
        'params': {'objective': 'reg:quantileerror', 'quantile_alpha': 0.90},
        'bias_adjustment': 0.0
    }
}

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("\n1. Loading Data...")
train_df = pd.read_csv("Data/processed/daily_train.csv")
val_df = pd.read_csv("Data/processed/daily_val.csv")  # Using Val set for evaluation

# Feature Prep
feature_cols = [c for c in train_df.columns if c not in EXCLUDE_FEATURES]
X_train, y_train = train_df[feature_cols], train_df[TARGET]
X_val, y_val = val_df[feature_cols], val_df[TARGET]

print(f"  ✓ Features: {len(feature_cols)}")
print(f"  ✓ Validation Samples: {len(X_val)}")
print(f"  ✓ Actual Flood Days in Val: {(y_val >= FLOOD_THRESHOLD).sum()}")


# =============================================================================
# 2. DEFINE CUSTOM METRICS
# =============================================================================
def calculate_safety_scorecard(y_true, y_pred, threshold=30.0):
    """Calculates Safety, Bias, and Operational metrics."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # 1. Confusion Matrix Components
    is_flood_actual = y_true >= threshold
    is_flood_pred = y_pred >= threshold

    TP = (is_flood_actual & is_flood_pred).sum()
    FP = (~is_flood_actual & is_flood_pred).sum()  # False Alarm
    FN = (is_flood_actual & ~is_flood_pred).sum()  # Missed Flood (DANGEROUS)
    TN = (~is_flood_actual & ~is_flood_pred).sum()

    # 2. Safety Metrics
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0

    # 3. Bias Metrics
    residuals = y_pred - y_true
    mean_bias = np.mean(residuals)  # Positive = Conservative

    # 4. Regime Specific RMSE
    flood_indices = y_true >= threshold
    if flood_indices.sum() > 0:
        flood_rmse = np.sqrt(mean_squared_error(y_true[flood_indices], y_pred[flood_indices]))
    else:
        flood_rmse = 0.0

    # 5. Operational Metrics
    far = FP / (TP + FP) if (TP + FP) > 0 else 0.0  # False Alarm Ratio
    csi = TP / (TP + FP + FN) if (TP + FP + FN) > 0 else 0.0  # Critical Success Index

    return {
        'Missed Floods (Count)': int(FN),
        'Recall (Safety)': round(recall, 3),
        'Mean Bias (ft)': round(mean_bias, 3),
        'False Alarms (Count)': int(FP),
        'False Alarm Ratio': round(far, 3),
        'Flood RMSE (ft)': round(flood_rmse, 3),
        'Overall RMSE (ft)': round(np.sqrt(mean_squared_error(y_true, y_pred)), 3)
    }


# =============================================================================
# 3. TRAIN AND EVALUATE MODELS
# =============================================================================
print("\n2. Training & Evaluating Models...")
results_list = []
predictions_dict = {}

base_params = {
    'n_estimators': 200, 'max_depth': 3, 'learning_rate': 0.05,
    'subsample': 0.8, 'n_jobs': -1, 'random_state': 42
}

for name, config in MODELS_CONFIG.items():
    print(f"  Training: {name}...")

    # Merge specific objective with base params
    params = {**base_params, **config['params']}

    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    # Predict and Adjust
    raw_preds = model.predict(X_val)
    final_preds = raw_preds + config['bias_adjustment']
    predictions_dict[name] = final_preds

    # Score
    scores = calculate_safety_scorecard(y_val, final_preds, FLOOD_THRESHOLD)
    scores['Model'] = name
    results_list.append(scores)

# Create Comparison DataFrame
scorecard_df = pd.DataFrame(results_list).set_index('Model')

# Reorder columns for logical flow
col_order = ['Missed Floods (Count)', 'Recall (Safety)', 'Mean Bias (ft)',
             'False Alarms (Count)', 'Flood RMSE (ft)', 'Overall RMSE (ft)']
scorecard_df = scorecard_df[col_order]

print("\n" + "=" * 80)
print("FINAL EVALUATION SCORECARD")
print("=" * 80)
print(scorecard_df)
print("=" * 80)

# =============================================================================
# 4. VISUALIZATION: THE SAFETY QUADRANT PLOT
# =============================================================================
print("\n3. Generating Safety Quadrant Plots...")
os.makedirs("Results/custom_eval", exist_ok=True)

fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True, sharex=True)

for i, (name, preds) in enumerate(predictions_dict.items()):
    ax = axes[i]

    # Define Quadrants
    # Q1 (Top Right): True Positive (Hit) - GREEN
    # Q2 (Bottom Right): False Negative (Miss) - RED (DANGER)
    # Q3 (Top Left): False Positive (False Alarm) - YELLOW
    # Q4 (Bottom Left): True Negative - GREY

    # Plot Logic
    ax.scatter(y_val, preds, alpha=0.5, c='grey', s=15, label='Normal')

    # Highlight Floods (Actual >= 30)
    flood_mask = y_val >= FLOOD_THRESHOLD

    # Hits (Green)
    hits = (y_val >= FLOOD_THRESHOLD) & (preds >= FLOOD_THRESHOLD)
    ax.scatter(y_val[hits], preds[hits], c='green', s=50, label='Detected Flood', edgecolors='black')

    # Misses (Red)
    misses = (y_val >= FLOOD_THRESHOLD) & (preds < FLOOD_THRESHOLD)
    ax.scatter(y_val[misses], preds[misses], c='red', s=80, marker='X', label='MISSED Flood', edgecolors='black')

    # False Alarms (Yellow)
    alarms = (y_val < FLOOD_THRESHOLD) & (preds >= FLOOD_THRESHOLD)
    ax.scatter(y_val[alarms], preds[alarms], c='orange', s=30, marker='s', label='False Alarm')

    # Draw Threshold Lines
    ax.axhline(FLOOD_THRESHOLD, color='black', linestyle='--', linewidth=2)
    ax.axvline(FLOOD_THRESHOLD, color='black', linestyle='--', linewidth=2)

    # Quadrant Labels
    ax.text(35, 35, "CORRECT\nDETECTION", color='green', fontweight='bold', ha='center')
    ax.text(35, 20, "DANGER ZONE\n(Missed)", color='red', fontweight='bold', ha='center')
    ax.text(15, 35, "FALSE ALARM\n(Cost)", color='orange', fontweight='bold', ha='center')

    ax.set_title(f"{name}\nMissed: {sum(misses)} | Bias: {np.mean(preds - y_val):.2f}ft", fontweight='bold')
    ax.set_xlabel("Actual Level (ft)")
    if i == 0: ax.set_ylabel("Predicted Level (ft)")
    ax.grid(True, alpha=0.3)

    # Force 1:1 aspect ratio line
    lims = [0, 45]
    ax.plot(lims, lims, 'k-', alpha=0.2, zorder=0)

    if name == 'Safety Quantile (q90)':
        model.save_model("Results/models/xgb_q90.json")
        print("  ✓ Saved XGBoost Artifact: Results/models/xgb_q90.json")

axes[2].legend(loc='lower right')
plt.tight_layout()
plt.savefig('Results/custom_eval/safety_quadrants.png', dpi=150)
print("  ✓ Saved: Results/custom_eval/safety_quadrants.png")

# Save Scorecard
scorecard_df.to_csv("Results/custom_eval/final_scorecard.csv")
print("  ✓ Saved: Results/custom_eval/final_scorecard.csv")
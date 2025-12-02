import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
import os

print("=" * 70)
print("PERSISTENCE BASELINE (THE 'NAIVE' MODEL)")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0
TARGET = 'target_level_max'

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("\n1. Loading Validation Data...")
# We use the validation set because that's what we evaluate on
val_df = pd.read_csv("Data/processed/daily_val.csv")
print(f"  ✓ Loaded {len(val_df)} days")

# =============================================================================
# 2. IDENTIFY LAG (1-DAY vs 2-DAY)
# =============================================================================
print("\n2. Identifying Lag Strategy...")

# We look for the "Lag 1" column. If it's missing (because we are in 48h mode),
# we fall back to "Lag 2".
if 'target_level_max_lag1d' in val_df.columns:
    lag_col = 'target_level_max_lag1d'
    print(f"  🔵 Detected 1-Day Lags. Using '{lag_col}' as prediction.")
    print("     (Logic: Tomorrow's Level = Today's Level)")
elif 'target_level_max_lag2d' in val_df.columns:
    lag_col = 'target_level_max_lag2d'
    print(f"  🔵 Detected 48h Lags. Using '{lag_col}' as prediction.")
    print("     (Logic: Day-After-Tomorrow's Level = Today's Level)")
else:
    raise ValueError("❌ Error: Could not find lag columns in dataset!")

# =============================================================================
# 3. GENERATE PREDICTIONS
# =============================================================================
# The "Model" is simply copying the column
y_val = val_df[TARGET]
y_pred = val_df[lag_col]

# Handle any NaNs (first few rows might be empty)
mask = ~y_pred.isna()
y_val = y_val[mask]
y_pred = y_pred[mask]


# =============================================================================
# 4. EVALUATION
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

    return {
        'Missed Floods': int(FN),
        'Recall': round(recall, 3),
        'False Alarms': int(FP),
        'Bias (ft)': round(np.mean(y_pred - y_true), 3),
        'RMSE (ft)': round(np.sqrt(mean_squared_error(y_true, y_pred)), 3)
    }


scores = calculate_safety_scorecard(y_val, y_pred, FLOOD_THRESHOLD)

print("\n" + "=" * 80)
print(f"PERSISTENCE SCORECARD (Using {lag_col})")
print("=" * 80)
print(pd.DataFrame([scores], index=['Persistence']).to_string())
print("=" * 80)

# =============================================================================
# 5. VISUALIZATION
# =============================================================================
os.makedirs("Results/persistence", exist_ok=True)

plt.figure(figsize=(12, 6))

# Zoom in on a dynamic period (e.g., 2019 flood)
zoom_start = 0
zoom_end = min(365, len(y_val))

plt.plot(range(zoom_end), y_val.iloc[zoom_start:zoom_end], 'k-', label='Actual', linewidth=2, alpha=0.8)
plt.plot(range(zoom_end), y_pred.iloc[zoom_start:zoom_end], 'g--', label='Persistence Prediction', linewidth=1.5)

plt.axhline(FLOOD_THRESHOLD, color='r', linestyle=':', label='Flood Stage')
plt.title(f"Persistence Baseline: Actual vs {lag_col}")
plt.ylabel("River Level (ft)")
plt.legend()
plt.grid(True, alpha=0.3)

plt.savefig('Results/persistence/persistence_check.png', dpi=150)
print(f"\n  ✓ Saved plot to Results/persistence/persistence_check.png")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os

print("=" * 70)
print("FINAL REPORT GENERATION (TEST SET 2023-2025)")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0
# CRITICAL: We now use the TEST set for the final verdict
DATA_FILE = "Data/processed/daily_test.csv"

EXCLUDE_FEATURES = [
    'date', 'time', 'target_level_max', 'target_level_mean',
    'target_level_min', 'target_level_std', 'target_level',
    'is_flood', 'is_major_flood', 'hermann_level', 'grafton_level'
]

# =============================================================================
# 1. LOAD TEST DATA
# =============================================================================
print(f"\n1. Loading TEST Data ({DATA_FILE})...")

# Check for 48h version first (Auto-detection)
if os.path.exists("Data/processed/daily_flood_dataset_48h_lags.csv"):
    # If the 48h file exists, we assume the test split was generated from it
    # If you aren't sure, regenerate splits!
    print("  ℹ Note: Assuming Test Data includes 48h lags.")

df = pd.read_csv(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])

# Prepare X and y
feature_cols = [c for c in df.columns if c not in EXCLUDE_FEATURES]
X_test = df[feature_cols].fillna(0)
y_test = df['target_level_max'].fillna(0)
dates = df['date']

print(f"  ✓ Test Samples: {len(df)}")
print(f"  ✓ Date Range: {dates.min().date()} to {dates.max().date()}")
print(f"  ✓ Flood Days in Test: {(y_test >= FLOOD_THRESHOLD).sum()}")

# =============================================================================
# 2. GENERATE BASELINES
# =============================================================================
print("\n2. Generating Baselines...")

# Persistence Logic (Auto-detect lag)
if 'target_level_max_lag1d' in df.columns:
    pred_persistence = df['target_level_max_lag1d'].fillna(0)
elif 'target_level_max_lag2d' in df.columns:
    pred_persistence = df['target_level_max_lag2d'].fillna(0)
else:
    pred_persistence = np.zeros_like(y_test)

# =============================================================================
# 3. LOAD MODELS & PREDICT
# =============================================================================
print("\n3. Loading Models & Predicting...")

preds = {'Persistence': pred_persistence}

# A. XGBoost
if os.path.exists("Results/models/xgb_q90.json"):
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model("Results/models/xgb_q90.json")
    preds['XGBoost (q90)'] = xgb_model.predict(X_test)

# B. Bayesian
if os.path.exists("Results/models/bayesian_model.pkl"):
    bayes_model = joblib.load("Results/models/bayesian_model.pkl")
    p_mean, p_std = bayes_model.predict(X_test, return_std=True)
    preds['Bayesian (Upper)'] = p_mean + (2 * p_std)

# C. LSTM
if os.path.exists("Results/models/lstm_q90.h5"):
    scaler_X = joblib.load("Results/models/lstm_scaler_X.pkl")
    scaler_y = joblib.load("Results/models/lstm_scaler_y.pkl")


    # Custom loss for loading
    def quantile_loss(q, y_true, y_pred):
        return tf.reduce_mean(tf.maximum(q * (y_true - y_pred), (q - 1) * (y_true - y_pred)))


    X_scaled = scaler_X.transform(X_test)
    X_lstm = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))
    lstm_model = load_model("Results/models/lstm_q90.h5",
                            custom_objects={'safety_loss': lambda y, p: quantile_loss(0.90, y, p)})

    p_scaled = lstm_model.predict(X_lstm, verbose=0)
    preds['LSTM (q90)'] = scaler_y.inverse_transform(p_scaled).flatten()

# D. Ensemble (Safety Max)
valid_models = [k for k in preds.keys() if k != 'Persistence']
if len(valid_models) >= 2:
    stack = np.column_stack([preds[m] for m in valid_models])
    preds['Ensemble (Max)'] = np.max(stack, axis=1)


# =============================================================================
# 4. FINAL SCORECARD (TEST SET)
# =============================================================================
def get_metrics(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    is_flood = y_true >= FLOOD_THRESHOLD
    is_pred = y_pred >= FLOOD_THRESHOLD

    TP = (is_flood & is_pred).sum()
    FN = (is_flood & ~is_pred).sum()  # Missed
    FP = (~is_flood & is_pred).sum()  # False Alarm

    return {
        'Missed Floods': int(FN),
        'Safety (Recall)': round(TP / (TP + FN), 3) if (TP + FN) > 0 else 0,
        'False Alarms': int(FP),
        'Mean Bias': round(np.mean(y_pred - y_true), 2),
        'RMSE': round(np.sqrt(mean_squared_error(y_true, y_pred)), 2)
    }


results = []
for name, p in preds.items():
    m = get_metrics(y_test, p)
    m['Model'] = name
    results.append(m)

df_res = pd.DataFrame(results).set_index('Model').sort_values('Missed Floods')
print("\n" + "=" * 80)
print("FINAL TEST SET SCORECARD (2023-2025)")
print("=" * 80)
print(df_res)
print("=" * 80)

# =============================================================================
# 5. REPORT VISUALIZATIONS
# =============================================================================
os.makedirs("Results/final_report", exist_ok=True)
print("\n4. Generating Report Visualizations...")

# --- PLOT 1: ERROR DISTRIBUTION (VIOLIN PLOT) ---
# Shows if the model is "Safe" (shifted positive) or "Accurate" (centered zero)
plt.figure(figsize=(12, 6))
residuals_data = []
for name, p in preds.items():
    resids = p - y_test
    # Downsample for speed if needed
    for r in resids:
        residuals_data.append({'Model': name, 'Residual (Pred - Actual)': r})

res_df = pd.DataFrame(residuals_data)
sns.violinplot(data=res_df, x='Model', y='Residual (Pred - Actual)', inner='quartile', palette="muted")
plt.axhline(0, color='black', linestyle='-', alpha=0.5)
plt.axhline(1.5, color='green', linestyle=':', label='Ideal Safety Buffer (+1.5ft)')
plt.title("Error Distribution: Positive Bias = Safer", fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig('Results/final_report/01_error_distribution.png', dpi=150)

# --- PLOT 2: CALIBRATION / COVERAGE CHECK ---
# For a q90 model, ~90% of actual data should be BELOW the prediction line.
plt.figure(figsize=(10, 6))
coverage_scores = []

for name, p in preds.items():
    # What % of Actual values are LESS THAN Predicted?
    coverage = (y_test <= p).mean() * 100
    coverage_scores.append({'Model': name, 'Coverage %': coverage})

cov_df = pd.DataFrame(coverage_scores).sort_values('Coverage %')
bars = plt.bar(cov_df['Model'], cov_df['Coverage %'], color='steelblue')
plt.axhline(90, color='red', linestyle='--', linewidth=2, label='Target Safety (90%)')
plt.axhline(50, color='gray', linestyle='--', label='Neutral (50%)')

# Add labels
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2., height,
             f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')

plt.ylim(0, 110)
plt.ylabel("Percent of Days Covered (Safe)", fontsize=11)
plt.title("Safety Verification: Are predictions actually conservative?", fontsize=14, fontweight='bold')
plt.xticks(rotation=15)
plt.legend()
plt.tight_layout()
plt.savefig('Results/final_report/02_safety_calibration.png', dpi=150)

# --- PLOT 3: FLOOD ROBUSTNESS (SENSITIVITY) ---
# How does the model perform if we change the flood definition?
thresholds = range(20, 32, 1)  # Test 20ft to 32ft
robustness_data = []

model_to_plot = 'Ensemble (Max)' if 'Ensemble (Max)' in preds else 'XGBoost (q90)'

for t in thresholds:
    is_flood = y_test
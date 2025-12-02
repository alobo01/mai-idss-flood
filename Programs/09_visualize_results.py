import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
import os

print("=" * 70)
print("GENERATING BEST-PRACTICE VISUALIZATIONS (FIXED LABELS)")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0
OUTPUT_DIR = "Results/Visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.4)

# =============================================================================
# 1. LOAD GLOBAL SUMMARY (METRICS)
# =============================================================================
print("1. Loading Summary Metrics...")
summary_file = "Results/Summary/global_comparison.csv"

if os.path.exists(summary_file):
    df_metrics = pd.read_csv(summary_file)
else:
    print("❌ Summary file not found. Please run '08_global_summary.py' first.")
    exit()

# =============================================================================
# 2. GENERATE PREDICTIONS FOR TIME SERIES PLOTS
# =============================================================================
print("2. Regenerating Predictions for Time Series Plots...")

all_preds = []

for lead_time in [1, 2, 3]:
    print(f"  Processing Lead Time: {lead_time} Days...")

    data_dir = f"Data/processed/L{lead_time}d"
    model_dir = f"Results/L{lead_time}d/models"

    if not os.path.exists(data_dir):
        continue

    test = pd.read_csv(f"{data_dir}/test.csv")
    test['date'] = pd.to_datetime(test['date'])

    EXCLUDE = ['date', 'time', 'target_level_max', 'target_level_mean',
               'target_level_min', 'target_level_std', 'target_level',
               'is_flood', 'is_major_flood']
    features = [c for c in test.columns if c not in EXCLUDE]

    X_test = test[features]

    # --- LOAD MODELS & PREDICT ---
    xgb_m = xgb.XGBRegressor()
    xgb_m.load_model(f"{model_dir}/xgb_q90.json")
    pred_xgb = xgb_m.predict(X_test)

    bayes_m = joblib.load(f"{model_dir}/bayes_model.pkl")
    bayes_s = joblib.load(f"{model_dir}/bayes_scaler.pkl")
    pred_bayes_mu, pred_bayes_std = bayes_m.predict(bayes_s.transform(X_test), return_std=True)
    pred_bayes = pred_bayes_mu + (2 * pred_bayes_std)


    def quantile_loss(q, y_true, y_pred):
        return tf.reduce_mean(tf.maximum(q * (y_true - y_pred), (q - 1) * (y_true - y_pred)))


    lstm_m = load_model(f"{model_dir}/lstm_q90.h5", custom_objects={'<lambda>': lambda y, p: quantile_loss(0.90, y, p)})
    lstm_sx = joblib.load(f"{model_dir}/lstm_scaler_x.pkl")
    lstm_sy = joblib.load(f"{model_dir}/lstm_scaler_y.pkl")

    X_lstm = lstm_sx.transform(X_test).reshape((len(X_test), 1, len(features)))
    pred_lstm = lstm_sy.inverse_transform(lstm_m.predict(X_lstm, verbose=0)).flatten()

    pred_ens = np.maximum(pred_xgb, np.maximum(pred_bayes, pred_lstm))

    df_pred = pd.DataFrame({
        'date': test['date'],
        'Actual': test['target_level_max'],
        'Ensemble': pred_ens,
        'Lead_Time': lead_time
    })
    all_preds.append(df_pred)

df_timeseries = pd.concat(all_preds)

# =============================================================================
# 3. PLOT 1: THE HYDROGRAPHS
# =============================================================================
print("3. Generating Hydrographs...")

fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)

for i, lead_time in enumerate([1, 2, 3]):
    ax = axes[i]
    data = df_timeseries[df_timeseries['Lead_Time'] == lead_time]

    ax.plot(data['date'], data['Actual'], color='black', label='Actual Level', linewidth=2, alpha=0.7)
    ax.plot(data['date'], data['Ensemble'], color='red', label='Ensemble Forecast', linewidth=1.5, linestyle='--')
    ax.axhline(FLOOD_THRESHOLD, color='orange', linestyle=':', linewidth=2, label='Flood Stage (30ft)')

    danger_zone = data[data['Ensemble'] < data['Actual']]
    ax.scatter(danger_zone['date'], danger_zone['Actual'], color='red', s=10, zorder=5, label='Under-prediction')

    ax.set_ylabel("River Level (ft)")
    ax.set_title(f"{lead_time}-Day Forecast Performance (2023-2025)", fontweight='bold', loc='left')
    ax.grid(True, alpha=0.3)
    if i == 0: ax.legend(loc='upper right', frameon=True)

plt.xlabel("Date")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_hydrographs_timeline.png", dpi=300)
print(f"  ✓ Saved {OUTPUT_DIR}/01_hydrographs_timeline.png")

# =============================================================================
# 4. PLOT 2: DEGRADATION CURVE
# =============================================================================
print("4. Generating Degradation Curves...")

fig, ax1 = plt.subplots(figsize=(10, 6))
models = df_metrics['Model'].unique()
markers = {'Ensemble': 'o', 'XGBoost': 's', 'LSTM': '^', 'Bayesian': 'D', 'Persistence': 'x'}
colors = {'Ensemble': 'red', 'XGBoost': 'blue', 'LSTM': 'green', 'Bayesian': 'purple', 'Persistence': 'gray'}

for model in models:
    subset = df_metrics[df_metrics['Model'] == model].sort_values('Lead Time')
    x = subset['Lead Time'].str.extract('(\d+)').astype(int)
    y = subset['RMSE']
    ax1.plot(x, y, marker=markers.get(model, 'o'), color=colors.get(model, 'black'),
             label=model, linewidth=2, markersize=8)

ax1.set_xlabel("Forecast Horizon (Days)")
ax1.set_ylabel("RMSE Error (ft)")
ax1.set_title("Forecast Degradation: Accuracy vs. Time", fontweight='bold')
ax1.set_xticks([1, 2, 3])
ax1.grid(True, alpha=0.3)
ax1.legend()
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_metric_degradation.png", dpi=300)
print(f"  ✓ Saved {OUTPUT_DIR}/02_metric_degradation.png")

# =============================================================================
# 5. PLOT 3: SAFETY TRADE-OFF (CLEAN BUBBLE STYLE)
# =============================================================================
print("5. Generating Safety Bubble Chart (Clean Style)...")
import matplotlib.patheffects as pe

plt.figure(figsize=(14, 9))

# Jitter points slightly to separate identical scores
# (We keep the jitter small so the label stays inside the dot)
jitter_x = np.random.uniform(-0.3, 0.3, size=len(df_metrics))
jitter_y = np.random.uniform(-0.05, 0.05, size=len(df_metrics))

# Define Colors
color_map = {
    'Ensemble': '#d62728',  # Red
    'XGBoost': '#1f77b4',  # Blue
    'LSTM': '#2ca02c',  # Green
    'Bayesian': '#9467bd',  # Purple
    'Persistence': '#7f7f7f'  # Gray
}

# Plot Bubbles
# s=600 makes them large enough to hold text
scatter = plt.scatter(
    df_metrics['False Alarms'] + jitter_x,
    df_metrics['Missed Floods'] + jitter_y,
    s=600,
    c=df_metrics['Model'].map(color_map),
    alpha=0.7,
    edgecolors='black',
    linewidth=1.5,
    zorder=2
)

# Reference Line
plt.axhline(0, color='green', linestyle='--', linewidth=2, label='Target: 0 Misses', zorder=1)

# --- CLEAN LABELING (INSIDE BUBBLE) ---
for i, row in df_metrics.iterrows():
    # Simplest Label: Just the Lead Time (e.g., "1d")
    # Extract digit from "1 Days" -> "1"
    days_digit = "".join(filter(str.isdigit, str(row['Lead Time'])))
    label = f"{days_digit}d"

    # Text Setup
    plt.text(
        row['False Alarms'] + jitter_x[i],
        row['Missed Floods'] + jitter_y[i],
        label,
        ha='center',
        va='center',
        fontsize=11,
        fontweight='bold',
        color='white',  # White text
        path_effects=[pe.withStroke(linewidth=2, foreground='black')],  # Black outline
        zorder=3
    )

# Add 5% padding so bubbles aren't cut off
plt.margins(0.05)

plt.xlabel("False Alarms (Operational Cost)", fontsize=14, fontweight='bold')
plt.ylabel("Missed Floods (Safety Risk)", fontsize=14, fontweight='bold')
plt.title("The Safety Trade-off: Risk vs. Cost", fontsize=16, fontweight='bold')
plt.grid(True, alpha=0.3)

# Manual Legend (To explain colors)
from matplotlib.lines import Line2D

legend_elements = [Line2D([0], [0], marker='o', color='w', label=k,
                          markerfacecolor=v, markersize=15, alpha=0.7, markeredgecolor='k')
                   for k, v in color_map.items()]

# Place legend outside or in empty corner
plt.legend(handles=legend_elements, loc='upper right', title="Model Type",
           frameon=True, framealpha=0.9, shadow=True, fontsize=12)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/03_safety_tradeoff.png", dpi=300)
print(f"  ✓ Saved {OUTPUT_DIR}/03_safety_tradeoff.png")

# =============================================================================
# 6. PLOT 4: ERROR DISTRIBUTION
# =============================================================================
print("6. Generating Bias Distribution...")

residuals_data = []
for lead_time in [1, 2, 3]:
    subset = df_timeseries[df_timeseries['Lead_Time'] == lead_time]
    resids = subset['Ensemble'] - subset['Actual']
    for r in resids:
        residuals_data.append({'Lead Time': f"{lead_time} Day", 'Error': r})

df_resid = pd.DataFrame(residuals_data)

plt.figure(figsize=(10, 6))
sns.violinplot(data=df_resid, x='Lead Time', y='Error', inner='quartile', palette="Reds")
plt.axhline(0, color='black', linestyle='-', linewidth=2)
plt.axhline(1.5, color='green', linestyle='--', label='Target Safety Buffer (+1.5ft)')
plt.ylabel("Prediction Error (Predicted - Actual)")
plt.title("Safety Bias Verification (Ensemble Model)", fontweight='bold')
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/04_bias_distribution.png", dpi=300)
print(f"  ✓ Saved {OUTPUT_DIR}/04_bias_distribution.png")

print("\n✓ VISUALIZATION COMPLETE.")
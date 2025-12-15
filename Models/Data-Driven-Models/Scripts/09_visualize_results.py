import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
import os
import matplotlib.patches as mpatches

print("=" * 70)
print("GENERATING VISUALIZATIONS: ORDERED & GAPPED BUTTERFLY CHART")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================
FLOOD_THRESHOLD = 30.0
OUTPUT_DIR = "Models/Data-Driven-Models/Results/Visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.4)

# =============================================================================
# 1. LOAD GLOBAL SUMMARY (METRICS)
# =============================================================================
print("1. Loading Summary Metrics...")
summary_file = "Models/Data-Driven-Models/Results/Summary/global_comparison.csv"

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
    model_dir = f"./L{lead_time}d/models"

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
# 5. PLOT 3: SAFETY TRADE-OFF (ORDERED + GAPPED)
# =============================================================================
print("5. Generating Safety Butterfly Chart (Explicit Layout)...")

# 1. Prepare Data
df_plot = df_metrics.copy()
df_plot['Lead_Day_Int'] = df_plot['Lead Time'].str.extract('(\d+)').astype(int)

# 2. DEFINE PLOTTING ORDER
# The user wants this specific order (Top to Bottom) within each group:
desired_model_order = ['LSTM', 'XGBoost', 'Ensemble', 'Bayesian', 'Persistence']

# We want groups ordered: 1 Day (Top), 2 Day (Middle), 3 Day (Bottom)
# Since 'barh' plots from y=0 upwards, y=0 is the bottom.
# So we need to calculate positions starting from the bottom-most group (3 Day)
group_order_bottom_to_top = [3, 2, 1]

# 3. CALCULATE Y-COORDINATES MANUALLY
plot_data = []
current_y = 0
gap_size = 2.5  # Size of gap between groups (1.0 = standard bar spacing)

for day in group_order_bottom_to_top:
    day_subset = df_plot[df_plot['Lead_Day_Int'] == day]

    # Within each group, we build from Bottom to Top.
    # If desired order is LSTM(Top)...Persistence(Bot),
    # then we must start plotting Persistence at y, then Bayesian at y+1, etc.
    # So we iterate the desired list in REVERSE.
    for model in reversed(desired_model_order):
        row = day_subset[day_subset['Model'] == model]
        if not row.empty:
            d = row.iloc[0].to_dict()
            d['y_pos'] = current_y
            plot_data.append(d)
            current_y += 1  # Move one slot up

    # After finishing a group, add the gap
    # (Subtract 1 because the loop adds 1 at the end, but we want 'gap_size' distance from the last bar)
    current_y += (gap_size - 1)

# Create a clean DataFrame for plotting based on these calculated positions
df_final = pd.DataFrame(plot_data)

# 4. PLOT
fig, ax = plt.subplots(figsize=(14, 12))

# Define Colors
model_colors = {
    'Ensemble': '#d62728',  # Red
    'XGBoost': '#1f77b4',  # Blue
    'LSTM': '#2ca02c',  # Green
    'Bayesian': '#9467bd',  # Purple
    'Persistence': '#7f7f7f'  # Gray
}

# Draw Bars using the explicit 'y_pos'
for i, row in df_final.iterrows():
    y = row['y_pos']
    c = model_colors.get(row['Model'], 'black')

    # Left Bar (Missed Floods)
    ax.barh(y, -row['Missed Floods'], color=c, alpha=0.85, height=0.6)

    # Right Bar (False Alarms)
    ax.barh(y, row['False Alarms'], color=c, alpha=0.85, height=0.6)

    # Add Value Labels
    # Left
    val_l = int(row['Missed Floods'])
    x_pos_l = -val_l - 1.5 if val_l > 0 else -0.5
    ax.text(x_pos_l, y, str(val_l), ha='right', va='center',
            fontsize=10, fontweight='bold', color=c)

    # Right
    val_r = int(row['False Alarms'])
    x_pos_r = val_r + 1.5
    ax.text(x_pos_r, y, str(val_r), ha='left', va='center',
            fontsize=10, fontweight='bold', color=c)

# Center Line
ax.axvline(0, color='black', linewidth=1)

# 5. Y-Axis Labels (Model Names)
ax.set_yticks(df_final['y_pos'])
ax.set_yticklabels(df_final['Model'], fontsize=11, fontweight='bold')

# 6. Group Labels (Horizon Names)
# Calculate the visual center of each group
for day in group_order_bottom_to_top:
    subset = df_final[df_final['Lead_Day_Int'] == day]
    if not subset.empty:
        # Average Y position of bars in this group
        center_y = subset['y_pos'].min()

        # Place label on the far left
        ax.text(-40, center_y, f"{day}d",
                ha='right', va='center', fontsize=14, fontweight='bold',
                color='#444444', style='italic')

        # Optional: Add faint separator line between groups
        # Find the gap below this group (min_y - something)
        # But since we have explicit gaps, we can just draw lines if needed.
        # Here we just leave the whitespace as requested.

# 7. Final Polish
xticks = ax.get_xticks()
ax.set_xticklabels([str(abs(int(x))) for x in xticks])
ax.set_xlim(-45, 110)  # Adjust as needed
ax.set_ylim(min(df_final['y_pos']) - 1, max(df_final['y_pos']) + 1)

ax.set_xlabel("← Missed Floods (Safety Risk)       |       False Alarms (Operational Cost) →",
              fontsize=13, fontweight='bold')
ax.set_title("Forecast Performance by Time Horizon (Ordered)", fontsize=16, fontweight='bold')

ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.grid(axis='y', alpha=0.0)

# Legend
legend_patches = [mpatches.Patch(color=model_colors[m], label=m) for m in desired_model_order]
ax.legend(handles=legend_patches, loc='upper right', title="Model Type",
          frameon=True, fontsize=11)

# Add space on left for the horizon labels
plt.subplots_adjust(left=0.18)

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
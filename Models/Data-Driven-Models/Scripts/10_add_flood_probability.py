import pandas as pd
import numpy as np
import argparse
import os
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import interp1d

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
args = parser.parse_args()

LEAD_TIME = args.days
DATA_DIR = f"Data/processed/L{LEAD_TIME}d"
RESULTS_DIR = f"./Results/L{LEAD_TIME}d"
VIZ_DIR = f"{RESULTS_DIR}/probability_plots"

print("=" * 70)
print(f"STEP 10: FLOOD PROBABILITY ESTIMATION (L{LEAD_TIME}d)")
print("=" * 70)

os.makedirs(VIZ_DIR, exist_ok=True)

# =============================================================================
# 1. LOAD PREDICTIONS WITH INTERVALS
# =============================================================================

print("\n1. Loading predictions with intervals...")

pred_file = f"{RESULTS_DIR}/predictions_with_intervals.csv"
if not os.path.exists(pred_file):
    print(f"  X {pred_file} not found!")
    print("  Run 08b_add_conformal_intervals.py first")
    exit()

pred_df = pd.read_csv(pred_file)
pred_df['date'] = pd.to_datetime(pred_df['date'])

print(f"  ✓ Loaded {len(pred_df)} predictions")

# =============================================================================
# 2. CALCULATE FLOOD PROBABILITY
# =============================================================================

FLOOD_THRESHOLD = 30.0  # flood level
print(f"\n2. Calculating flood probability (threshold: {FLOOD_THRESHOLD} ft)...")

# Quick sanity check
print("\n  Quantile prediction ranges:")
print(f"    q10: {pred_df['ensemble_q10'].min():.1f} - {pred_df['ensemble_q10'].max():.1f} ft")
print(f"    q50: {pred_df['ensemble_q50'].min():.1f} - {pred_df['ensemble_q50'].max():.1f} ft")
print(f"    q90: {pred_df['ensemble_q90'].min():.1f} - {pred_df['ensemble_q90'].max():.1f} ft")
print(f"    Actual: {pred_df['actual'].min():.1f} - {pred_df['actual'].max():.1f} ft")

# Check how often q90 exceeds threshold
print(f"\n  q90 > {FLOOD_THRESHOLD} ft: {(pred_df['ensemble_q90'] > FLOOD_THRESHOLD).sum()} times")


def calculate_flood_probability(row, threshold):
    """
    Estimate P(level > threshold) using quantile predictions.

    Uses linear interpolation between quantiles:
    - q10, q50, q90 define the predictive distribution
    - Interpolate to find probability that level exceeds threshold
    """
    q10 = row['ensemble_q10']
    q50 = row['ensemble_q50']
    q90 = row['ensemble_q90']

    # Define quantile points (probability that actual < predicted)
    quantiles = np.array([0.10, 0.50, 0.90])
    levels = np.array([q10, q50, q90])

    # Check boundary cases
    if threshold <= q10:
        # Threshold below even the 10th percentile → very high probability
        return 0.95
    elif threshold >= q90:
        # Threshold above 90th percentile → very low probability
        return 0.05
    else:
        # Interpolate to find quantile corresponding to threshold
        # Create interpolation function: level → quantile
        interp_func = interp1d(levels, quantiles,
                               kind='linear',
                               fill_value='extrapolate')

        # Find P(level < threshold)
        prob_below = float(interp_func(threshold))

        # Clamp to [0, 1]
        prob_below = np.clip(prob_below, 0.0, 1.0)

        # We want P(level > threshold)
        prob_above = 1.0 - prob_below

        return prob_above


# Apply to all predictions
pred_df['flood_probability'] = pred_df.apply(
    lambda row: calculate_flood_probability(row, FLOOD_THRESHOLD),
    axis=1
)

print(f"  ✓ Calculated flood probabilities")
print(f"  Mean probability: {pred_df['flood_probability'].mean():.2%}")
print(f"  Max probability:  {pred_df['flood_probability'].max():.2%}")
print(f"  High risk days (P>50%): {(pred_df['flood_probability'] > 0.5).sum()}")

# =============================================================================
# 3. ADD TO ORIGINAL DATASETS
# =============================================================================

print("\n3. Adding flood probability to train/val/test datasets...")

# Load original splits
train_df = pd.read_csv(f"{DATA_DIR}/train.csv")
val_df = pd.read_csv(f"{DATA_DIR}/val.csv")
test_df = pd.read_csv(f"{DATA_DIR}/test.csv")

train_df['date'] = pd.to_datetime(train_df['date'])
val_df['date'] = pd.to_datetime(val_df['date'])
test_df['date'] = pd.to_datetime(test_df['date'])

# Merge flood probability (only test has it)
test_df = test_df.merge(
    pred_df[['date', 'flood_probability', 'ensemble_q10', 'ensemble_q50', 'ensemble_q90',
             'conformal_lower', 'conformal_median', 'conformal_upper']],
    on='date',
    how='left'
)

# For train/val, we don't have predictions, so set to NaN or calculate from actual
# (In real deployment, you'd retrain and predict on these too)
train_df['flood_probability'] = np.nan
val_df['flood_probability'] = np.nan

# Save updated datasets
train_df.to_csv(f"{DATA_DIR}/train_with_prob.csv", index=False)
val_df.to_csv(f"{DATA_DIR}/val_with_prob.csv", index=False)
test_df.to_csv(f"{DATA_DIR}/test_with_prob.csv", index=False)

print(f"  ✓ Saved updated datasets to {DATA_DIR}/")

# =============================================================================
# 4. CREATE DUAL-AXIS VISUALIZATION
# =============================================================================

print("\n4. Creating dual-axis visualization...")

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.3)

# -----------------------------------------------------------------------------
# PLOT 1: FULL TIMELINE WITH PROBABILITY
# -----------------------------------------------------------------------------

fig, ax1 = plt.subplots(figsize=(18, 8))

# Left axis: River level
color_level = 'steelblue'
ax1.set_xlabel('Date', fontsize=14, fontweight='bold')
ax1.set_ylabel('River Level (ft)', fontsize=14, fontweight='bold', color=color_level)

# Prediction interval (shaded)
ax1.fill_between(
    pred_df['date'],
    pred_df['conformal_lower'],
    pred_df['conformal_upper'],
    alpha=0.2,
    color='skyblue',
    label='80% Prediction Interval'
)

# Actual level
ax1.plot(pred_df['date'], pred_df['actual'],
         color='black', linewidth=2, label='Actual Level', alpha=0.8)

# Median forecast
ax1.plot(pred_df['date'], pred_df['conformal_median'],
         color='blue', linewidth=2, linestyle='--', label='Forecast (Median)', alpha=0.7)

# Flood threshold
ax1.axhline(FLOOD_THRESHOLD, color='darkred', linestyle=':',
            linewidth=2.5, label=f'Flood Stage ({FLOOD_THRESHOLD} ft)', alpha=0.7)

ax1.tick_params(axis='y', labelcolor=color_level)
ax1.set_ylim([pred_df['actual'].min() - 2, pred_df['actual'].max() + 2])
ax1.grid(True, alpha=0.3)

# Right axis: Flood probability
ax2 = ax1.twinx()
color_prob = 'crimson'

ax2.set_ylabel('Flood Probability', fontsize=14, fontweight='bold', color=color_prob)
ax2.plot(pred_df['date'], pred_df['flood_probability'],
         color=color_prob, linewidth=2.5, label='Flood Probability', alpha=0.8)

# Shade high-risk areas
high_risk = pred_df['flood_probability'] > 0.5
if high_risk.any():
    # Get continuous segments of high risk
    ax2.fill_between(pred_df['date'], 0, pred_df['flood_probability'],
                     where=high_risk,
                     alpha=0.2, color='red',
                     label='High Risk (P>50%)')

ax2.tick_params(axis='y', labelcolor=color_prob)
ax2.set_ylim([0, 1])
ax2.axhline(0.5, color='orange', linestyle='--', linewidth=1.5, alpha=0.5)

# Title and legends
plt.title(f'{LEAD_TIME}-Day Forecast: River Level and Flood Probability (>{FLOOD_THRESHOLD} ft)',
          fontsize=16, fontweight='bold', pad=20)

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc='upper left', fontsize=11, frameon=True, framealpha=0.9)

plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/01_level_and_probability_timeline.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 01_level_and_probability_timeline.png")

# -----------------------------------------------------------------------------
# PLOT 2: ZOOMED VIEW ON HIGH-RISK PERIOD
# -----------------------------------------------------------------------------

# Find high-risk periods
high_risk_mask = pred_df['flood_probability'] > 0.3

if high_risk_mask.any():
    print("\n5. Creating zoomed high-risk period view...")

    # Get date range
    risk_dates = pred_df[high_risk_mask]['date']
    start_date = risk_dates.min() - pd.Timedelta(days=30)
    end_date = risk_dates.max() + pd.Timedelta(days=30)

    zoom_df = pred_df[(pred_df['date'] >= start_date) & (pred_df['date'] <= end_date)]

    if len(zoom_df) > 0:
        fig, ax1 = plt.subplots(figsize=(16, 8))

        # Left axis: River level
        ax1.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax1.set_ylabel('River Level (ft)', fontsize=14, fontweight='bold', color='steelblue')

        # Prediction interval
        ax1.fill_between(zoom_df['date'], zoom_df['conformal_lower'], zoom_df['conformal_upper'],
                         alpha=0.2, color='skyblue', label='80% Prediction Interval')

        # Actual and forecast
        ax1.plot(zoom_df['date'], zoom_df['actual'], 'k-', linewidth=2.5, label='Actual Level')
        ax1.plot(zoom_df['date'], zoom_df['conformal_median'], 'b--', linewidth=2, label='Forecast')

        # Threshold
        ax1.axhline(FLOOD_THRESHOLD, color='darkred', linestyle=':', linewidth=2.5,
                    label=f'Major Flood ({FLOOD_THRESHOLD} ft)')

        # Danger zone shading
        ax1.axhspan(FLOOD_THRESHOLD, zoom_df['actual'].max() + 5,
                    alpha=0.05, color='red', zorder=-1)

        ax1.tick_params(axis='y', labelcolor='steelblue')
        ax1.grid(True, alpha=0.3)

        # Right axis: Probability
        ax2 = ax1.twinx()
        ax2.set_ylabel('Flood Probability', fontsize=14, fontweight='bold', color='crimson')
        ax2.plot(zoom_df['date'], zoom_df['flood_probability'],
                 color='crimson', linewidth=3, label='Flood Probability', marker='o', markersize=4)

        # Mark high risk days
        high_risk_zoom = zoom_df['flood_probability'] > 0.5
        ax2.scatter(zoom_df[high_risk_zoom]['date'],
                    zoom_df[high_risk_zoom]['flood_probability'],
                    color='red', s=100, zorder=5, label='High Risk', edgecolors='black', linewidth=1.5)

        ax2.axhline(0.5, color='orange', linestyle='--', linewidth=2, alpha=0.6, label='50% Threshold')
        ax2.tick_params(axis='y', labelcolor='crimson')
        ax2.set_ylim([0, 1])

        # Title
        plt.title(f'{LEAD_TIME}-Day Forecast: High-Risk Period Detail',
                  fontsize=16, fontweight='bold', pad=20)

        # Legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2,
                   loc='upper left', fontsize=11, frameon=True, framealpha=0.9)

        plt.tight_layout()
        plt.savefig(f'{VIZ_DIR}/02_high_risk_period_zoom.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: 02_high_risk_period_zoom.png")

# -----------------------------------------------------------------------------
# PLOT 3: PROBABILITY CALIBRATION
# -----------------------------------------------------------------------------

print("\n6. Creating probability calibration plot...")

# Bin by predicted probability
prob_bins = np.linspace(0, 1, 11)  # 0-10%, 10-20%, ..., 90-100%
bin_centers = (prob_bins[:-1] + prob_bins[1:]) / 2

observed_freq = []
predicted_freq = []
counts = []

for i in range(len(prob_bins) - 1):
    mask = (pred_df['flood_probability'] >= prob_bins[i]) & \
           (pred_df['flood_probability'] < prob_bins[i + 1])

    if mask.sum() > 0:
        # Predicted: mean probability in bin
        predicted_freq.append(pred_df[mask]['flood_probability'].mean())

        # Observed: actual flood frequency
        observed_freq.append((pred_df[mask]['actual'] >= FLOOD_THRESHOLD).mean())

        counts.append(mask.sum())
    else:
        predicted_freq.append(bin_centers[i])
        observed_freq.append(np.nan)
        counts.append(0)

fig, ax = plt.subplots(figsize=(10, 10))

# Perfect calibration line
ax.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Perfect Calibration', alpha=0.5)

# Actual calibration
valid = ~np.isnan(observed_freq)
ax.scatter(np.array(predicted_freq)[valid], np.array(observed_freq)[valid],
           s=np.array(counts)[valid] * 5,  # Size by sample count
           c=np.array(counts)[valid], cmap='Reds',
           edgecolors='black', linewidth=1.5, alpha=0.7,
           label='Observed Frequency')

# Connect points
ax.plot(np.array(predicted_freq)[valid], np.array(observed_freq)[valid],
        'b-', linewidth=2, alpha=0.5)

# Add sample counts as text
for i, (pred, obs, count) in enumerate(zip(predicted_freq, observed_freq, counts)):
    if not np.isnan(obs) and count > 0:
        ax.text(pred, obs + 0.03, f'n={count}',
                ha='center', fontsize=9, fontweight='bold')

ax.set_xlabel('Predicted Flood Probability', fontsize=14, fontweight='bold')
ax.set_ylabel('Observed Flood Frequency', fontsize=14, fontweight='bold')
ax.set_title(f'{LEAD_TIME}-Day Forecast: Probability Calibration (Threshold: {FLOOD_THRESHOLD} ft)',
             fontsize=15, fontweight='bold')
ax.set_xlim([0, 1])
ax.set_ylim([0, 1])
ax.grid(True, alpha=0.3)
ax.legend(fontsize=12)

# Add colorbar
sm = plt.cm.ScalarMappable(cmap='Reds',
                           norm=plt.Normalize(vmin=0, vmax=max(counts)))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax)
cbar.set_label('Sample Count', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/03_probability_calibration.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 03_probability_calibration.png")

# -----------------------------------------------------------------------------
# PLOT 4: DECISION SUPPORT MATRIX
# -----------------------------------------------------------------------------

print("\n7. Creating decision support matrix...")


# Create risk categories
def categorize_risk(row):
    prob = row['flood_probability']
    actual = row['actual']

    if prob >= 0.7:
        forecast = 'High Risk'
    elif prob >= 0.3:
        forecast = 'Moderate Risk'
    else:
        forecast = 'Low Risk'

    if actual >= FLOOD_THRESHOLD:
        outcome = 'Flood Occurred'
    else:
        outcome = 'No Flood'

    return forecast, outcome


pred_df['forecast_category'], pred_df['outcome_category'] = zip(*pred_df.apply(categorize_risk, axis=1))

# Contingency table
contingency = pd.crosstab(pred_df['forecast_category'], pred_df['outcome_category'])

fig, ax = plt.subplots(figsize=(10, 8))

# Heatmap
sns.heatmap(contingency, annot=True, fmt='d', cmap='YlOrRd',
            cbar_kws={'label': 'Count'},
            linewidths=2, linecolor='black',
            square=True, ax=ax)

ax.set_xlabel('Actual Outcome', fontsize=14, fontweight='bold')
ax.set_ylabel('Forecast Risk Level', fontsize=14, fontweight='bold')
ax.set_title(f'{LEAD_TIME}-Day Forecast: Decision Support Matrix (Threshold: {FLOOD_THRESHOLD} ft)',
             fontsize=15, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/04_decision_support_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 04_decision_support_matrix.png")

# =============================================================================
# 8. SUMMARY STATISTICS
# =============================================================================

print("\n" + "=" * 70)
print("FLOOD PROBABILITY SUMMARY")
print("=" * 70)

print(f"\n📊 Probability Statistics:")
print(f"  Mean:   {pred_df['flood_probability'].mean():.2%}")
print(f"  Median: {pred_df['flood_probability'].median():.2%}")
print(f"  Max:    {pred_df['flood_probability'].max():.2%}")
print(f"  Std:    {pred_df['flood_probability'].std():.2%}")

print(f"\n📊 Risk Categories:")
high_risk = (pred_df['flood_probability'] >= 0.7).sum()
mod_risk = ((pred_df['flood_probability'] >= 0.3) & (pred_df['flood_probability'] < 0.7)).sum()
low_risk = (pred_df['flood_probability'] < 0.3).sum()

print(f"  High Risk (≥70%):   {high_risk} days ({high_risk / len(pred_df) * 100:.1f}%)")
print(f"  Moderate (30-70%):  {mod_risk} days ({mod_risk / len(pred_df) * 100:.1f}%)")
print(f"  Low Risk (<30%):    {low_risk} days ({low_risk / len(pred_df) * 100:.1f}%)")

print(f"\n📊 Actual Flood Events (≥{FLOOD_THRESHOLD} ft):")
actual_floods = (pred_df['actual'] >= FLOOD_THRESHOLD).sum()
print(f"  Total: {actual_floods} days ({actual_floods / len(pred_df) * 100:.1f}%)")

if actual_floods > 0:
    # How many were predicted?
    caught_high = ((pred_df['actual'] >= FLOOD_THRESHOLD) &
                   (pred_df['flood_probability'] >= 0.7)).sum()
    caught_mod = ((pred_df['actual'] >= FLOOD_THRESHOLD) &
                  (pred_df['flood_probability'] >= 0.3)).sum()

    print(
        f"  Caught by high risk forecast:     {caught_high}/{actual_floods} ({caught_high / actual_floods * 100:.0f}%)")
    print(
        f"  Caught by moderate+ risk forecast: {caught_mod}/{actual_floods} ({caught_mod / actual_floods * 100:.0f}%)")

print(f"\n✅ All outputs saved to:")
print(f"  - Datasets: {DATA_DIR}/*_with_prob.csv")
print(f"  - Plots: {VIZ_DIR}/")

print("\n" + "=" * 70)
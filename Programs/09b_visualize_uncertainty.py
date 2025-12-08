import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
import joblib

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
args = parser.parse_args()

LEAD_TIME = args.days
RESULTS_DIR = f"Results/L{LEAD_TIME}d"
VIZ_DIR = f"{RESULTS_DIR}/uncertainty_plots"

print("=" * 70)
print(f"STEP 09b: UNCERTAINTY VISUALIZATION (L{LEAD_TIME}d)")
print("=" * 70)

os.makedirs(VIZ_DIR, exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.3)

# =============================================================================
# 1. LOAD DATA
# =============================================================================

pred_df = pd.read_csv(f"{RESULTS_DIR}/predictions_with_intervals.csv")
pred_df['date'] = pd.to_datetime(pred_df['date'])
calibration = joblib.load(f"{RESULTS_DIR}/calibration_info.pkl")

print(f"  ✓ Loaded {len(pred_df)} predictions")

FLOOD_THRESHOLD = 30.0

# =============================================================================
# 2. PLOT 1: FULL TIMELINE WITH PREDICTION INTERVALS
# =============================================================================

print("\n1. Creating timeline with uncertainty bands...")

fig, ax = plt.subplots(figsize=(18, 8))

# Conformal prediction interval (shaded band)
ax.fill_between(
    pred_df['date'],
    pred_df['conformal_lower'],
    pred_df['conformal_upper'],
    alpha=0.3,
    color='skyblue',
    label=f'{int((1-calibration["alpha"])*100)}% Prediction Interval'
)

# Actual values
ax.plot(pred_df['date'], pred_df['actual'], 
        color='black', linewidth=2, label='Actual', alpha=0.8)

# Median prediction
ax.plot(pred_df['date'], pred_df['conformal_median'],
        color='red', linewidth=2, linestyle='--', label='Forecast (Median)', alpha=0.8)

# Flood threshold
ax.axhline(FLOOD_THRESHOLD, color='orange', linestyle=':', 
          linewidth=2.5, label='Flood Stage (30 ft)', alpha=0.7)

# Highlight where actual exceeds upper bound (dangerous under-prediction)
danger_mask = pred_df['actual'] > pred_df['conformal_upper']
if danger_mask.any():
    ax.scatter(pred_df[danger_mask]['date'], pred_df[danger_mask]['actual'],
              color='darkred', s=30, zorder=5, label='Above Upper Bound', alpha=0.8)

ax.set_xlabel('Date', fontsize=14, fontweight='bold')
ax.set_ylabel('River Level (ft)', fontsize=14, fontweight='bold')
ax.set_title(f'{LEAD_TIME}-Day Forecast with Conformal Prediction Intervals\n'
            f'Coverage: {calibration["test_coverage_conformal"]:.1%} (Target: {int((1-calibration["alpha"])*100)}%)',
            fontsize=16, fontweight='bold')
ax.legend(fontsize=11, loc='upper left', frameon=True, framealpha=0.9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/01_timeline_with_intervals.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 01_timeline_with_intervals.png")

# =============================================================================
# 3. PLOT 2: ZOOMED VIEW (HIGH-RISK PERIOD)
# =============================================================================

print("\n2. Creating zoomed view of critical period...")

# Find periods with floods or near-floods
critical_mask = pred_df['actual'] >= FLOOD_THRESHOLD - 5
critical_periods = pred_df[critical_mask]

if len(critical_periods) > 0:
    # Get date range around critical events
    start_date = critical_periods['date'].min() - pd.Timedelta(days=30)
    end_date = critical_periods['date'].max() + pd.Timedelta(days=30)
    
    zoom_df = pred_df[(pred_df['date'] >= start_date) & (pred_df['date'] <= end_date)]
    
    fig, ax = plt.subplots(figsize=(16, 7))
    
    # Prediction interval
    ax.fill_between(zoom_df['date'], zoom_df['conformal_lower'], zoom_df['conformal_upper'],
                    alpha=0.3, color='skyblue', label='80% Prediction Interval')
    
    # Actual and forecast
    ax.plot(zoom_df['date'], zoom_df['actual'], 'k-', linewidth=2.5, label='Actual')
    ax.plot(zoom_df['date'], zoom_df['conformal_median'], 'r--', linewidth=2, label='Forecast')
    
    # Flood threshold
    ax.axhline(FLOOD_THRESHOLD, color='orange', linestyle=':', linewidth=2.5, label='Flood Stage')
    
    # Danger zone shading
    ax.axhspan(FLOOD_THRESHOLD, pred_df['actual'].max(), alpha=0.1, color='red')
    
    ax.set_xlabel('Date', fontsize=13, fontweight='bold')
    ax.set_ylabel('River Level (ft)', fontsize=13, fontweight='bold')
    ax.set_title(f'{LEAD_TIME}-Day Forecast: Critical Period Detail',
                fontsize=15, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{VIZ_DIR}/02_critical_period_zoom.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: 02_critical_period_zoom.png")
else:
    print("  ⚠️  No critical periods found (no floods in test set)")

# =============================================================================
# 4. PLOT 3: CALIBRATION PLOT (COVERAGE BY RIVER LEVEL)
# =============================================================================

print("\n3. Creating calibration diagnostic plot...")

# Bin by actual river level
bins = np.linspace(pred_df['actual'].min(), pred_df['actual'].max(), 15)
bin_centers = (bins[:-1] + bins[1:]) / 2
bin_indices = np.digitize(pred_df['actual'], bins)

coverage_by_level = []
count_by_level = []

for i in range(1, len(bins)):
    mask = bin_indices == i
    if mask.sum() > 0:
        in_interval = ((pred_df[mask]['actual'] >= pred_df[mask]['conformal_lower']) &
                      (pred_df[mask]['actual'] <= pred_df[mask]['conformal_upper']))
        coverage_by_level.append(in_interval.mean())
        count_by_level.append(mask.sum())
    else:
        coverage_by_level.append(np.nan)
        count_by_level.append(0)

fig, ax = plt.subplots(figsize=(12, 7))

# Coverage bars
bars = ax.bar(bin_centers, coverage_by_level, width=bins[1]-bins[0], 
             alpha=0.7, edgecolor='black')

# Color bars by sample size
colors = plt.cm.Blues(np.array(count_by_level) / max(count_by_level))
for bar, color in zip(bars, colors):
    bar.set_facecolor(color)

# Target coverage line
ax.axhline(1 - calibration['alpha'], color='red', linestyle='--', 
          linewidth=2.5, label=f'Target Coverage ({int((1-calibration["alpha"])*100)}%)')

# Flood threshold
ax.axvline(FLOOD_THRESHOLD, color='orange', linestyle=':', 
          linewidth=2, label='Flood Stage', alpha=0.7)

ax.set_xlabel('Actual River Level (ft)', fontsize=13, fontweight='bold')
ax.set_ylabel('Empirical Coverage', fontsize=13, fontweight='bold')
ax.set_title(f'{LEAD_TIME}-Day Forecast: Coverage Calibration by River Level',
            fontsize=15, fontweight='bold')
ax.set_ylim([0, 1.05])
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

# Add count labels on top of bars
for i, (x, y, count) in enumerate(zip(bin_centers, coverage_by_level, count_by_level)):
    if not np.isnan(y) and count > 0:
        ax.text(x, y + 0.02, f'n={count}', ha='center', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/03_calibration_by_level.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 03_calibration_by_level.png")

# =============================================================================
# 5. PLOT 4: INTERVAL WIDTH ANALYSIS
# =============================================================================

print("\n4. Creating interval width analysis...")

# Calculate interval widths
pred_df['interval_width'] = pred_df['conformal_upper'] - pred_df['conformal_lower']

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) Width over time
axes[0, 0].plot(pred_df['date'], pred_df['interval_width'], linewidth=1.5, color='steelblue')
axes[0, 0].axhline(pred_df['interval_width'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {pred_df["interval_width"].mean():.1f} ft')
axes[0, 0].set_xlabel('Date')
axes[0, 0].set_ylabel('Interval Width (ft)')
axes[0, 0].set_title('(a) Prediction Interval Width Over Time')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# (b) Width vs actual level
axes[0, 1].scatter(pred_df['actual'], pred_df['interval_width'], 
                   alpha=0.5, s=20, c=pred_df['actual'], cmap='RdYlBu_r')
axes[0, 1].axvline(FLOOD_THRESHOLD, color='orange', linestyle=':', linewidth=2, alpha=0.7)
axes[0, 1].set_xlabel('Actual River Level (ft)')
axes[0, 1].set_ylabel('Interval Width (ft)')
axes[0, 1].set_title('(b) Interval Width vs. River Level')
axes[0, 1].grid(True, alpha=0.3)

# (c) Width distribution
axes[1, 0].hist(pred_df['interval_width'], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
axes[1, 0].axvline(pred_df['interval_width'].mean(), color='red', linestyle='--', linewidth=2)
axes[1, 0].set_xlabel('Interval Width (ft)')
axes[1, 0].set_ylabel('Count')
axes[1, 0].set_title('(c) Distribution of Interval Widths')
axes[1, 0].grid(True, alpha=0.3, axis='y')

# (d) Coverage by width quartile
width_quartiles = pd.qcut(pred_df['interval_width'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
coverage_by_quartile = []

for q in ['Q1', 'Q2', 'Q3', 'Q4']:
    mask = width_quartiles == q
    in_interval = ((pred_df[mask]['actual'] >= pred_df[mask]['conformal_lower']) &
                  (pred_df[mask]['actual'] <= pred_df[mask]['conformal_upper']))
    coverage_by_quartile.append(in_interval.mean())

axes[1, 1].bar(['Q1\n(Narrow)', 'Q2', 'Q3', 'Q4\n(Wide)'], coverage_by_quartile, 
              color='steelblue', alpha=0.7, edgecolor='black')
axes[1, 1].axhline(1 - calibration['alpha'], color='red', linestyle='--', linewidth=2)
axes[1, 1].set_ylabel('Coverage')
axes[1, 1].set_title('(d) Coverage by Width Quartile')
axes[1, 1].set_ylim([0, 1.05])
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.suptitle(f'{LEAD_TIME}-Day Forecast: Prediction Interval Analysis', 
            fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/04_interval_width_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 04_interval_width_analysis.png")

# =============================================================================
# 6. PLOT 5: MODEL COMPARISON (UNCALIBRATED vs CONFORMAL)
# =============================================================================

print("\n5. Creating calibration improvement comparison...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Sample period for visualization (first 100 days)
sample_df = pred_df.head(100)

# (a) Uncalibrated
axes[0].fill_between(sample_df['date'], sample_df['ensemble_q10'], sample_df['ensemble_q90'],
                    alpha=0.3, color='lightcoral', label='Uncalibrated Interval')
axes[0].plot(sample_df['date'], sample_df['actual'], 'k-', linewidth=2, label='Actual')
axes[0].plot(sample_df['date'], sample_df['ensemble_q50'], 'b--', linewidth=1.5, label='Median')
axes[0].axhline(FLOOD_THRESHOLD, color='orange', linestyle=':', linewidth=2, alpha=0.7)

# Mark points outside interval
outside = ((sample_df['actual'] < sample_df['ensemble_q10']) | 
          (sample_df['actual'] > sample_df['ensemble_q90']))
axes[0].scatter(sample_df[outside]['date'], sample_df[outside]['actual'],
               color='red', s=40, zorder=5, label=f'Outside ({outside.sum()})')

axes[0].set_ylabel('River Level (ft)')
axes[0].set_title(f'(a) Uncalibrated\nCoverage: {calibration["test_coverage_uncalibrated"]:.1%}')
axes[0].legend(fontsize=9)
axes[0].grid(True, alpha=0.3)
axes[0].tick_params(axis='x', rotation=45)

# (b) Conformal
axes[1].fill_between(sample_df['date'], sample_df['conformal_lower'], sample_df['conformal_upper'],
                    alpha=0.3, color='skyblue', label='Conformal Interval')
axes[1].plot(sample_df['date'], sample_df['actual'], 'k-', linewidth=2, label='Actual')
axes[1].plot(sample_df['date'], sample_df['conformal_median'], 'r--', linewidth=1.5, label='Median')
axes[1].axhline(FLOOD_THRESHOLD, color='orange', linestyle=':', linewidth=2, alpha=0.7)

# Mark points outside interval
outside_conf = ((sample_df['actual'] < sample_df['conformal_lower']) | 
               (sample_df['actual'] > sample_df['conformal_upper']))
axes[1].scatter(sample_df[outside_conf]['date'], sample_df[outside_conf]['actual'],
               color='red', s=40, zorder=5, label=f'Outside ({outside_conf.sum()})')

axes[1].set_ylabel('River Level (ft)')
axes[1].set_title(f'(b) Conformal Calibrated\nCoverage: {calibration["test_coverage_conformal"]:.1%} ✓')
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)
axes[1].tick_params(axis='x', rotation=45)

plt.suptitle(f'{LEAD_TIME}-Day Forecast: Conformal Calibration Effect (First 100 Days)',
            fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{VIZ_DIR}/05_calibration_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ Saved: 05_calibration_comparison.png")

# =============================================================================
# 7. SUMMARY STATISTICS
# =============================================================================

print("\n" + "=" * 70)
print("UNCERTAINTY QUANTIFICATION SUMMARY")
print("=" * 70)

print(f"\n📊 Prediction Interval Statistics:")
print(f"  Mean width: {pred_df['interval_width'].mean():.2f} ft")
print(f"  Std width:  {pred_df['interval_width'].std():.2f} ft")
print(f"  Min width:  {pred_df['interval_width'].min():.2f} ft")
print(f"  Max width:  {pred_df['interval_width'].max():.2f} ft")

print(f"\n📊 Coverage:")
print(f"  Target:          {int((1-calibration['alpha'])*100)}%")
print(f"  Uncalibrated:    {calibration['test_coverage_uncalibrated']:.1%}")
print(f"  Conformal:       {calibration['test_coverage_conformal']:.1%}")

# Safety metrics
exceeds_upper = (pred_df['actual'] > pred_df['conformal_upper']).sum()
below_lower = (pred_df['actual'] < pred_df['conformal_lower']).sum()

print(f"\n📊 Safety Analysis:")
print(f"  Above upper bound: {exceeds_upper} ({exceeds_upper/len(pred_df)*100:.1f}%)")
print(f"  Below lower bound: {below_lower} ({below_lower/len(pred_df)*100:.1f}%)")

# Flood-specific
flood_actual = (pred_df['actual'] >= FLOOD_THRESHOLD).sum()
flood_caught = ((pred_df['actual'] >= FLOOD_THRESHOLD) & 
               (pred_df['conformal_lower'] >= FLOOD_THRESHOLD)).sum()
flood_warned = ((pred_df['actual'] >= FLOOD_THRESHOLD) & 
               (pred_df['conformal_median'] >= FLOOD_THRESHOLD)).sum()

if flood_actual > 0:
    print(f"\n📊 Flood Detection (actual ≥{FLOOD_THRESHOLD} ft):")
    print(f"  Flood events: {flood_actual}")
    print(f"  Lower bound caught: {flood_caught} ({flood_caught/flood_actual*100:.0f}%)")
    print(f"  Median forecast caught: {flood_warned} ({flood_warned/flood_actual*100:.0f}%)")

print(f"\n✅ All visualizations saved to: {VIZ_DIR}/")
print("\n" + "=" * 70)
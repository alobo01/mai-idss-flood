import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import os

print("=" * 70)
print("WEATHER-ONLY MODEL (NO UPSTREAM STATIONS)")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET = 'target_level_max'

# Features to EXCLUDE
EXCLUDE_FEATURES = [
    'date', 'time',
    'target_level_max', 'target_level_mean', 'target_level_min', 'target_level_std',
    'target_level',
    'is_flood', 'is_major_flood',
    # NEW: Exclude all upstream station features
    'hermann_level', 'grafton_level',
]

# Keywords to identify weather features
WEATHER_KEYWORDS = [
    'precip', 'precipitation', 'rain', 'snow',
    'temp', 'temperature',
    'soil', 'moisture',
    'humidity', 'wind',
    'heavy_rain'
]

# Keywords to identify upstream features (to exclude)
UPSTREAM_KEYWORDS = [
    'hermann', 'grafton'
]

# Base hyperparameters
BASE_PARAMS = {
    'max_depth': 3,
    'learning_rate': 0.05,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'n_jobs': -1
}

# =============================================================================
# 1. LOAD DATA
# =============================================================================

print("\n1. Loading data...")

train_df = pd.read_csv("Data/processed/daily_train.csv")
val_df = pd.read_csv("Data/processed/daily_val.csv")
test_df = pd.read_csv("Data/processed/daily_test.csv")

train_df['date'] = pd.to_datetime(train_df['date'])
val_df['date'] = pd.to_datetime(val_df['date'])
test_df['date'] = pd.to_datetime(test_df['date'])

print(f"  ✓ Train: {len(train_df)} days")
print(f"  ✓ Val:   {len(val_df)} days")
print(f"  ✓ Test:  {len(test_df)} days")

# For 3-year visualization
three_years_start = pd.to_datetime('2022-01-01')
train_subset = train_df[train_df['date'] >= three_years_start].copy()
viz_df = pd.concat([train_subset, val_df, test_df], ignore_index=True)
viz_df = viz_df.sort_values('date').reset_index(drop=True)

# =============================================================================
# 2. FEATURE SELECTION - WEATHER ONLY
# =============================================================================

print("\n2. Selecting weather-only features...")

all_columns = train_df.columns.tolist()

# Step 1: Remove explicit exclusions
candidate_features = [col for col in all_columns if col not in EXCLUDE_FEATURES]

# Step 2: Remove any upstream features
weather_only_features = []
upstream_features = []

for col in candidate_features:
    # Check if it's an upstream feature
    is_upstream = any(keyword in col.lower() for keyword in UPSTREAM_KEYWORDS)
    
    if is_upstream:
        upstream_features.append(col)
    else:
        weather_only_features.append(col)

print(f"\n  Feature breakdown:")
print(f"    Total columns: {len(all_columns)}")
print(f"    Excluded (targets, dates): {len(EXCLUDE_FEATURES)}")
print(f"    Upstream features (removed): {len(upstream_features)}")
print(f"    Weather + target lags (keeping): {len(weather_only_features)}")

# Show what we're excluding
print(f"\n  Upstream features being excluded:")
for feat in upstream_features[:10]:  # Show first 10
    print(f"    - {feat}")
if len(upstream_features) > 10:
    print(f"    ... and {len(upstream_features) - 10} more")

# Show what we're keeping
print(f"\n  Key weather features being used:")
weather_features = [f for f in weather_only_features if any(kw in f.lower() for kw in WEATHER_KEYWORDS)]
for feat in weather_features[:10]:
    print(f"    - {feat}")

target_lag_features = [f for f in weather_only_features if 'target_level_lag' in f]
print(f"\n  Autoregressive features (target history):")
for feat in target_lag_features:
    print(f"    - {feat}")

# =============================================================================
# 3. PREPARE DATA
# =============================================================================

print("\n3. Preparing datasets...")

X_train = train_df[weather_only_features]
y_train = train_df[TARGET]

X_val = val_df[weather_only_features]
y_val = val_df[TARGET]

X_viz = viz_df[weather_only_features]
y_viz = viz_df[TARGET]

print(f"  ✓ X_train shape: {X_train.shape}")
print(f"  ✓ Feature count: {len(weather_only_features)}")

# =============================================================================
# 4. TRAIN WEATHER-ONLY MODEL
# =============================================================================

print("\n4. Training weather-only model...")
print("=" * 70)

model = xgb.XGBRegressor(**BASE_PARAMS)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)

# Predictions
y_pred_train = model.predict(X_train)
y_pred_val = model.predict(X_val)
y_pred_viz = model.predict(X_viz)

# Metrics
train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
train_mae = mean_absolute_error(y_train, y_pred_train)
val_mae = mean_absolute_error(y_val, y_pred_val)
train_r2 = r2_score(y_train, y_pred_train)
val_r2 = r2_score(y_val, y_pred_val)

print(f"\n  Weather-only model results:")
print(f"    Train RMSE: {train_rmse:.2f} ft, MAE: {train_mae:.2f} ft, R²: {train_r2:.3f}")
print(f"    Val   RMSE: {val_rmse:.2f} ft, MAE: {val_mae:.2f} ft, R²: {val_r2:.3f}")

# =============================================================================
# 5. LOAD BASELINE MODEL FOR COMPARISON
# =============================================================================

print("\n5. Loading baseline model (with upstream) for comparison...")

try:
    baseline_model = xgb.XGBRegressor()
    baseline_model.load_model('Results/models/best_regression_model.json')
    
    # Get baseline features (with upstream)
    baseline_comparison = pd.read_csv('Results/models/model_comparison.csv')
    baseline_rmse = baseline_comparison['Val RMSE'].min()
    baseline_r2 = baseline_comparison['Val R²'].max()
    
    print(f"  Baseline (with upstream):")
    print(f"    Val RMSE: {baseline_rmse:.2f} ft")
    print(f"    Val R²:   {baseline_r2:.3f}")
    
    print(f"\n  ⚠️  Performance degradation:")
    print(f"    RMSE increased: {val_rmse - baseline_rmse:.2f} ft ({(val_rmse/baseline_rmse - 1)*100:.1f}% worse)")
    print(f"    R² decreased: {val_r2 - baseline_r2:.3f} ({(baseline_r2 - val_r2)/baseline_r2*100:.1f}% worse)")
    
    has_baseline = True
except:
    print("  ⚠️  Baseline model not found (run 06_baseline_model.py first)")
    has_baseline = False

# =============================================================================
# 6. VISUALIZATIONS
# =============================================================================

print("\n6. Creating visualizations...")
os.makedirs("Results/models", exist_ok=True)

# Plot 1: 3-year time series comparison
fig, axes = plt.subplots(2, 1, figsize=(20, 10), sharex=True)

viz_dates = viz_df['date'].values

# Top: Weather-only model
axes[0].plot(viz_dates, y_viz.values, label='Actual', linewidth=2, alpha=0.8, color='blue')
axes[0].plot(viz_dates, y_pred_viz, label='Weather-only Prediction', linewidth=2, alpha=0.8, color='red', linestyle='--')
axes[0].axhline(y=30, color='orange', linestyle=':', linewidth=2, alpha=0.7, label='Flood Stage')
axes[0].axhline(y=40, color='darkred', linestyle=':', linewidth=2, alpha=0.7, label='Major Flood')
axes[0].axvline(x=pd.to_datetime('2023-01-01'), color='green', linestyle='--', linewidth=2, alpha=0.5)
axes[0].axvline(x=pd.to_datetime('2024-01-01'), color='purple', linestyle='--', linewidth=2, alpha=0.5)
axes[0].set_ylabel('River Level (ft)', fontsize=13, fontweight='bold')
axes[0].set_title(f'Weather-Only Model (3-Year Timeline)\nVal RMSE: {val_rmse:.2f} ft | MAE: {val_mae:.2f} ft | R²: {val_r2:.3f}', 
                  fontsize=14, fontweight='bold')
axes[0].legend(fontsize=11, loc='upper left')
axes[0].grid(True, alpha=0.3)

# Bottom: Residuals
residuals = y_viz.values - y_pred_viz
axes[1].plot(viz_dates, residuals, linewidth=1, alpha=0.7, color='purple')
axes[1].axhline(y=0, color='black', linestyle='--', linewidth=2)
axes[1].axhline(y=val_mae, color='red', linestyle=':', linewidth=1, alpha=0.5, label=f'±MAE ({val_mae:.2f} ft)')
axes[1].axhline(y=-val_mae, color='red', linestyle=':', linewidth=1, alpha=0.5)
axes[1].axvline(x=pd.to_datetime('2023-01-01'), color='green', linestyle='--', linewidth=2, alpha=0.5, label='Val Start')
axes[1].axvline(x=pd.to_datetime('2024-01-01'), color='purple', linestyle='--', linewidth=2, alpha=0.5, label='Test Start')
axes[1].set_ylabel('Residual (ft)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Date', fontsize=13, fontweight='bold')
axes[1].set_title('Prediction Residuals (Actual - Predicted)', fontsize=14, fontweight='bold')
axes[1].legend(fontsize=11, loc='upper left')
axes[1].grid(True, alpha=0.3)

import matplotlib.dates as mdates
axes[1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('Results/models/weather_only_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: weather_only_timeseries.png")

# Plot 2: Scatter and residuals
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Scatter
axes[0, 0].scatter(y_val, y_pred_val, alpha=0.5, s=10)
axes[0, 0].plot([y_val.min(), y_val.max()], [y_val.min(), y_val.max()], 'r--', lw=2)
axes[0, 0].set_xlabel('Actual Level (ft)', fontsize=11)
axes[0, 0].set_ylabel('Predicted Level (ft)', fontsize=11)
axes[0, 0].set_title('Weather-Only: Predictions vs Actual', fontweight='bold', fontsize=12)
axes[0, 0].grid(True, alpha=0.3)

# Residuals vs predicted
val_residuals = y_val.values - y_pred_val
axes[0, 1].scatter(y_pred_val, val_residuals, alpha=0.5, s=10)
axes[0, 1].axhline(y=0, color='r', linestyle='--', lw=2)
axes[0, 1].set_xlabel('Predicted Level (ft)', fontsize=11)
axes[0, 1].set_ylabel('Residual (ft)', fontsize=11)
axes[0, 1].set_title('Residual Plot', fontweight='bold', fontsize=12)
axes[0, 1].grid(True, alpha=0.3)

# Residual histogram
axes[1, 0].hist(val_residuals, bins=50, edgecolor='black', alpha=0.7)
axes[1, 0].axvline(x=0, color='r', linestyle='--', lw=2)
axes[1, 0].set_xlabel('Residual (ft)', fontsize=11)
axes[1, 0].set_ylabel('Count', fontsize=11)
axes[1, 0].set_title(f'Residual Distribution\nMean: {val_residuals.mean():.2f} ft | Std: {val_residuals.std():.2f} ft', 
                     fontweight='bold', fontsize=12)
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Error by actual value
bins = np.linspace(y_val.min(), y_val.max(), 20)
bin_centers = (bins[:-1] + bins[1:]) / 2
abs_errors = np.abs(val_residuals)
bin_indices = np.digitize(y_val, bins)

mean_abs_errors = []
for i in range(1, len(bins)):
    mask = bin_indices == i
    if mask.sum() > 0:
        mean_abs_errors.append(abs_errors[mask].mean())
    else:
        mean_abs_errors.append(np.nan)

axes[1, 1].plot(bin_centers, mean_abs_errors, marker='o', linewidth=2, markersize=6)
axes[1, 1].set_xlabel('Actual River Level (ft)', fontsize=11)
axes[1, 1].set_ylabel('Mean Absolute Error (ft)', fontsize=11)
axes[1, 1].set_title('Prediction Error by River Level', fontweight='bold', fontsize=12)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Results/models/weather_only_diagnostics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: weather_only_diagnostics.png")

# Plot 3: Feature importance
feature_importance = model.feature_importances_
importance_df = pd.DataFrame({
    'feature': weather_only_features,
    'importance': feature_importance
}).sort_values('importance', ascending=False).head(20)

fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(importance_df['feature'], importance_df['importance'])
ax.set_xlabel('Importance', fontsize=11)
ax.set_title('Top 20 Weather Feature Importances', fontsize=12, fontweight='bold')
ax.invert_yaxis()
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('Results/models/weather_only_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: weather_only_feature_importance.png")

# Plot 4: Comparison with baseline (if available)
if has_baseline:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    models = ['With Upstream\n(Baseline)', 'Weather Only']
    rmse_vals = [baseline_rmse, val_rmse]
    r2_vals = [baseline_r2, val_r2]
    
    axes[0].bar(models, rmse_vals, color=['green', 'orange'])
    axes[0].set_ylabel('RMSE (ft)', fontsize=11)
    axes[0].set_title('Validation RMSE Comparison', fontweight='bold', fontsize=12)
    axes[0].grid(True, alpha=0.3, axis='y')
    
    axes[1].bar(models, r2_vals, color=['green', 'orange'])
    axes[1].set_ylabel('R²', fontsize=11)
    axes[1].set_title('Validation R² Comparison', fontweight='bold', fontsize=12)
    axes[1].grid(True, alpha=0.3, axis='y')
    
    # Feature count
    baseline_feature_count = len([f for f in all_columns if f not in EXCLUDE_FEATURES])
    feature_counts = [baseline_feature_count, len(weather_only_features)]
    
    axes[2].bar(models, feature_counts, color=['green', 'orange'])
    axes[2].set_ylabel('Feature Count', fontsize=11)
    axes[2].set_title('Number of Features Used', fontweight='bold', fontsize=12)
    axes[2].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('Results/models/weather_vs_baseline_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: weather_vs_baseline_comparison.png")

# =============================================================================
# 7. SAVE RESULTS
# =============================================================================

print("\n7. Saving results...")

model.save_model('Results/models/weather_only_model.json')
print("  ✓ Saved: weather_only_model.json")

importance_df.to_csv('Results/models/weather_only_top_features.csv', index=False)
print("  ✓ Saved: weather_only_top_features.csv")

# Save feature list
with open('Results/models/weather_only_features.txt', 'w') as f:
    f.write("WEATHER-ONLY MODEL FEATURES\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Total features: {len(weather_only_features)}\n\n")
    f.write("Weather features:\n")
    for feat in weather_features:
        f.write(f"  - {feat}\n")
    f.write(f"\nTarget lag features:\n")
    for feat in target_lag_features:
        f.write(f"  - {feat}\n")
    f.write(f"\nExcluded upstream features:\n")
    for feat in upstream_features:
        f.write(f"  - {feat}\n")
print("  ✓ Saved: weather_only_features.txt")

# =============================================================================
# 8. SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("WEATHER-ONLY MODEL SUMMARY")
print("=" * 70)

print(f"\n📊 Model Performance:")
print(f"    Val RMSE: {val_rmse:.2f} ft")
print(f"    Val MAE:  {val_mae:.2f} ft")
print(f"    Val R²:   {val_r2:.3f}")

print(f"\n📊 Features Used:")
print(f"    Total: {len(weather_only_features)}")
print(f"    Weather: {len(weather_features)}")
print(f"    Target lags: {len(target_lag_features)}")
print(f"    Excluded upstream: {len(upstream_features)}")

print(f"\n🔝 Top 3 Features:")
for i, row in importance_df.head(3).iterrows():
    print(f"    {i+1}. {row['feature']}")

if has_baseline:
    print(f"\n📉 vs Baseline (with upstream):")
    print(f"    RMSE: {val_rmse:.2f} vs {baseline_rmse:.2f} (+{val_rmse - baseline_rmse:.2f} ft)")
    print(f"    R²:   {val_r2:.3f} vs {baseline_r2:.3f} ({(baseline_r2 - val_r2):.3f} worse)")
    print(f"\n💡 Upstream stations provide {(baseline_r2 - val_r2)/baseline_r2*100:.1f}% of predictive power")


print("\n" + "=" * 70)
print("WEATHER-ONLY ANALYSIS COMPLETE!")
print("=" * 70)
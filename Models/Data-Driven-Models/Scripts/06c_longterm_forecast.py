import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import os

print("=" * 70)
print("MULTI-HORIZON WEATHER-BASED FORECAST (1-7 DAYS AHEAD)")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET = 'target_level_max'
FORECAST_HORIZONS = [1, 2, 3]  # Days ahead to forecast

# Features to EXCLUDE
EXCLUDE_FEATURES = [
    'date', 'time',
    'target_level_max', 'target_level_mean', 'target_level_min', 'target_level_std',
    'target_level',
    'is_flood', 'is_major_flood',
]

# Upstream features to exclude (weather-only model)
UPSTREAM_KEYWORDS = ['hermann', 'grafton']

# Base hyperparameters
BASE_PARAMS = {
    'max_depth': 4,
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

# For visualization
three_years_start = pd.to_datetime('2022-01-01')
train_subset = train_df[train_df['date'] >= three_years_start].copy()
viz_df = pd.concat([train_subset, val_df, test_df], ignore_index=True)
viz_df = viz_df.sort_values('date').reset_index(drop=True)

# =============================================================================
# 2. FEATURE PREPARATION
# =============================================================================

print("\n2. Preparing features for multi-horizon forecasting...")

all_columns = train_df.columns.tolist()

# Remove explicit exclusions and upstream features
candidate_features = [col for col in all_columns if col not in EXCLUDE_FEATURES]
base_features = [col for col in candidate_features
                 if not any(kw in col.lower() for kw in UPSTREAM_KEYWORDS)]

print(f"\n  Base features (weather + all target lags): {len(base_features)}")

# Identify lag features for dynamic filtering
target_lag_features = [f for f in base_features if 'lag' in f and 'target' in f and 'd' in f]

# Parse lag days from feature names
lag_info = []
for feat in target_lag_features:
    # Extract number before 'd' (e.g., 'target_level_lag3d' -> 3)
    try:
        lag_days = int(feat.split('lag')[1].split('d')[0])
        lag_info.append({'feature': feat, 'lag_days': lag_days})
    except:
        pass

lag_df = pd.DataFrame(lag_info)

print(f"  Target lag features: {len(lag_df)}")
if len(lag_df) > 0:
    print(f"  Lag range: {lag_df['lag_days'].min()}-{lag_df['lag_days'].max()} days")

# =============================================================================
# 3. CREATE TARGETS FOR EACH HORIZON
# =============================================================================

print("\n3. Creating shifted targets for each forecast horizon...")

# For each horizon, create target = value k days in the future
for k in FORECAST_HORIZONS:
    train_df[f'target_{k}d_ahead'] = train_df[TARGET].shift(-k)
    val_df[f'target_{k}d_ahead'] = val_df[TARGET].shift(-k)
    viz_df[f'target_{k}d_ahead'] = viz_df[TARGET].shift(-k)

# Drop rows where targets are NaN (end of dataset)
train_df = train_df.dropna(subset=[f'target_{k}d_ahead' for k in FORECAST_HORIZONS])
val_df = val_df.dropna(subset=[f'target_{k}d_ahead' for k in FORECAST_HORIZONS])

print(f"  ✓ Created targets for horizons: {FORECAST_HORIZONS}")
print(f"  ✓ Train samples after shift: {len(train_df)}")
print(f"  ✓ Val samples after shift: {len(val_df)}")

# =============================================================================
# 4. TRAIN MODELS FOR EACH HORIZON
# =============================================================================

print("\n4. Training multi-horizon models...")
print("=" * 70)

results = {}

for k in FORECAST_HORIZONS:
    print(f"\n{'=' * 70}")
    print(f"Forecast Horizon: {k} day(s) ahead")
    print(f"{'=' * 70}")

    # Select features: exclude lags < k days (they're in the future!)
    if len(lag_df) > 0:
        valid_lags = lag_df[lag_df['lag_days'] >= k]['feature'].tolist()
        invalid_lags = lag_df[lag_df['lag_days'] < k]['feature'].tolist()
    else:
        valid_lags = []
        invalid_lags = []

    # Weather features (no lags)
    weather_features = [f for f in base_features if 'lag' not in f or f in valid_lags]

    print(f"\n  Feature selection:")
    print(f"    Total base features: {len(base_features)}")
    print(f"    Valid target lags (≥{k}d): {len(valid_lags)}")
    print(f"    Excluded target lags (<{k}d): {len(invalid_lags)}")
    print(f"    Final features: {len(weather_features)}")

    if len(invalid_lags) > 0 and k <= 3:
        print(f"    Excluded (future data): {', '.join(invalid_lags[:5])}")

    # Prepare data
    X_train = train_df[weather_features]
    y_train = train_df[f'target_{k}d_ahead']

    X_val = val_df[weather_features]
    y_val = val_df[f'target_{k}d_ahead']

    # Train model
    model = xgb.XGBRegressor(**BASE_PARAMS)

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    # Predictions
    y_pred_val = model.predict(X_val)

    # Metrics
    val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
    val_mae = mean_absolute_error(y_val, y_pred_val)
    val_r2 = r2_score(y_val, y_pred_val)

    print(f"\n  Results:")
    print(f"    Val RMSE: {val_rmse:.2f} ft")
    print(f"    Val MAE:  {val_mae:.2f} ft")
    print(f"    Val R²:   {val_r2:.3f}")

    # Feature importance
    feature_importance = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': weather_features,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)

    top_feature = importance_df.iloc[0]['feature']
    print(f"    Top feature: {top_feature}")

    # Store results
    results[k] = {
        'model': model,
        'features': weather_features,
        'val_rmse': val_rmse,
        'val_mae': val_mae,
        'val_r2': val_r2,
        'predictions': y_pred_val,
        'actuals': y_val,
        'importance': importance_df,
    }

# =============================================================================
# 5. ANALYZE PERFORMANCE DEGRADATION
# =============================================================================

print("\n" + "=" * 70)
print("5. Analyzing forecast degradation over horizon...")
print("=" * 70)

degradation_data = []
for k in FORECAST_HORIZONS:
    degradation_data.append({
        'Horizon (days)': k,
        'RMSE (ft)': results[k]['val_rmse'],
        'MAE (ft)': results[k]['val_mae'],
        'R²': results[k]['val_r2'],
        'Features': len(results[k]['features'])
    })

degradation_df = pd.DataFrame(degradation_data)
print("\n" + degradation_df.to_string(index=False))

print("\n📉 Performance Degradation:")
baseline_rmse = results[1]['val_rmse']
baseline_r2 = results[1]['val_r2']

for k in FORECAST_HORIZONS[1:]:  # Skip first (baseline)
    rmse_increase = results[k]['val_rmse'] - baseline_rmse
    r2_decrease = baseline_r2 - results[k]['val_r2']
    print(f"  {k}-day vs 1-day:")
    print(f"    RMSE: +{rmse_increase:.2f} ft ({rmse_increase / baseline_rmse * 100:.1f}% worse)")
    print(f"    R²: -{r2_decrease:.3f} ({r2_decrease / baseline_r2 * 100:.1f}% worse)")

# =============================================================================
# 6. VISUALIZATIONS
# =============================================================================

print("\n6. Creating visualizations...")
os.makedirs("Models/Data-Driven-Models/Results/models", exist_ok=True)

# Plot 1: Performance vs Horizon
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

horizons = degradation_df['Horizon (days)']

axes[0].plot(horizons, degradation_df['RMSE (ft)'], marker='o', linewidth=2, markersize=8)
axes[0].set_xlabel('Forecast Horizon (days)', fontsize=11, fontweight='bold')
axes[0].set_ylabel('RMSE (ft)', fontsize=11, fontweight='bold')
axes[0].set_title('Forecast Error vs Horizon', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3)

axes[1].plot(horizons, degradation_df['MAE (ft)'], marker='s', linewidth=2, markersize=8, color='orange')
axes[1].set_xlabel('Forecast Horizon (days)', fontsize=11, fontweight='bold')
axes[1].set_ylabel('MAE (ft)', fontsize=11, fontweight='bold')
axes[1].set_title('Mean Absolute Error vs Horizon', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

axes[2].plot(horizons, degradation_df['R²'], marker='^', linewidth=2, markersize=8, color='green')
axes[2].set_xlabel('Forecast Horizon (days)', fontsize=11, fontweight='bold')
axes[2].set_ylabel('R²', fontsize=11, fontweight='bold')
axes[2].set_title('R² vs Horizon', fontsize=12, fontweight='bold')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/models/multihorizon_performance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: multihorizon_performance.png")

# Plot 2: Example forecasts for different horizons (validation set sample)
sample_start = pd.to_datetime('2023-06-01')
sample_end = pd.to_datetime('2023-08-31')

sample_mask = (val_df['date'] >= sample_start) & (val_df['date'] <= sample_end)
sample_dates = val_df[sample_mask]['date'].values
sample_actual = val_df[sample_mask][TARGET].values

fig, ax = plt.subplots(figsize=(18, 8))

ax.plot(sample_dates, sample_actual, label='Actual', linewidth=2.5, alpha=0.9, color='blue')

colors = ['red', 'orange', 'green', 'purple', 'brown']
for i, k in enumerate(FORECAST_HORIZONS):
    sample_pred = results[k]['predictions'][sample_mask.values]
    ax.plot(sample_dates, sample_pred,
            label=f'{k}-day forecast (RMSE: {results[k]["val_rmse"]:.2f} ft)',
            linewidth=1.5, alpha=0.7, linestyle='--', color=colors[i])

ax.axhline(y=30, color='orange', linestyle=':', linewidth=2, alpha=0.5, label='Flood Stage')
ax.set_xlabel('Date', fontsize=13, fontweight='bold')
ax.set_ylabel('River Level (ft)', fontsize=13, fontweight='bold')
ax.set_title('Multi-Horizon Forecasts: Summer 2023 (Validation Period)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.grid(True, alpha=0.3)

import matplotlib.dates as mdates

ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/models/multihorizon_example_forecasts.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: multihorizon_example_forecasts.png")

# Plot 2: Full 3-year timeline with all horizons
viz_df_clean = viz_df.dropna(subset=[f'target_{k}d_ahead' for k in FORECAST_HORIZONS])
X_viz_clean = viz_df_clean[weather_features]  # Will need to define weather_features earlier

fig, ax = plt.subplots(figsize=(20, 8))

viz_dates = viz_df_clean['date'].values
y_viz_actual = viz_df_clean[TARGET].values

ax.plot(viz_dates, y_viz_actual, label='Actual', linewidth=2.5, alpha=0.9, color='blue')

colors = ['red', 'orange', 'green']
for i, k in enumerate(FORECAST_HORIZONS):
    # Get predictions for full 3-year period
    X_viz_for_k = viz_df_clean[results[k]['features']]
    y_pred_viz = results[k]['model'].predict(X_viz_for_k)

    ax.plot(viz_dates, y_pred_viz,
            label=f'{k}-day forecast (RMSE: {results[k]["val_rmse"]:.2f} ft)',
            linewidth=1.5, alpha=0.7, linestyle='--', color=colors[i])

ax.axhline(y=30, color='orange', linestyle=':', linewidth=2, alpha=0.5, label='Flood Stage')
ax.axvline(x=pd.to_datetime('2023-01-01'), color='green', linestyle='--', linewidth=2, alpha=0.5, label='Val Start')
ax.axvline(x=pd.to_datetime('2024-01-01'), color='purple', linestyle='--', linewidth=2, alpha=0.5, label='Test Start')

ax.set_xlabel('Date', fontsize=13, fontweight='bold')
ax.set_ylabel('River Level (ft)', fontsize=13, fontweight='bold')
ax.set_title('Multi-Horizon Forecasts: 3-Year Timeline (2022-2025)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.grid(True, alpha=0.3)

import matplotlib.dates as mdates

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/models/multihorizon_3year_timeline.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: multihorizon_3year_timeline.png")

# Plot 3: Feature importance comparison across horizons
fig, axes = plt.subplots(1, len(FORECAST_HORIZONS), figsize=(20, 6))

for i, k in enumerate(FORECAST_HORIZONS):
    top_features = results[k]['importance'].head(10)

    axes[i].barh(top_features['feature'], top_features['importance'])
    axes[i].set_title(f'{k}-Day Forecast', fontsize=11, fontweight='bold')
    axes[i].set_xlabel('Importance', fontsize=10)
    axes[i].invert_yaxis()
    axes[i].grid(True, alpha=0.3, axis='x')

    # Smaller font for feature names
    axes[i].tick_params(axis='y', labelsize=8)

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/models/multihorizon_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: multihorizon_feature_importance.png")

# Plot 4: Prediction scatter for each horizon
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i, k in enumerate(FORECAST_HORIZONS):
    y_actual = results[k]['actuals']
    y_pred = results[k]['predictions']

    axes[i].scatter(y_actual, y_pred, alpha=0.3, s=5)
    axes[i].plot([y_actual.min(), y_actual.max()],
                 [y_actual.min(), y_actual.max()],
                 'r--', lw=2)
    axes[i].set_xlabel('Actual Level (ft)', fontsize=10)
    axes[i].set_ylabel('Predicted Level (ft)', fontsize=10)
    axes[i].set_title(f'{k}-Day Forecast\nRMSE: {results[k]["val_rmse"]:.2f} ft, R²: {results[k]["val_r2"]:.3f}',
                      fontsize=11, fontweight='bold')
    axes[i].grid(True, alpha=0.3)

# Hide unused subplot
if len(FORECAST_HORIZONS) < 6:
    axes[-1].axis('off')

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/models/multihorizon_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: multihorizon_scatter.png")

# =============================================================================
# 7. SAVE RESULTS
# =============================================================================

print("\n7. Saving results...")

degradation_df.to_csv('Models/Data-Driven-Models/Results/models/multihorizon_performance.csv', index=False)
print("  ✓ Saved: multihorizon_performance.csv")

for k in FORECAST_HORIZONS:
    results[k]['model'].save_model(f'Models/Data-Driven-Models/Results/multihorizon_model_{k}d.json')
    results[k]['importance'].head(20).to_csv(f'Models/Data-Driven-Models/Results/multihorizon_features_{k}d.csv', index=False)

print(f"  ✓ Saved: {len(FORECAST_HORIZONS)} models and feature lists")

# =============================================================================
# 8. SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("MULTI-HORIZON FORECAST SUMMARY")
print("=" * 70)

print(f"\n📊 Forecast Horizons: {FORECAST_HORIZONS} days")
print(f"📊 Models trained: {len(FORECAST_HORIZONS)}")
print(f"📊 Validation samples: {len(val_df)}")

print("\n🎯 PERFORMANCE BY HORIZON:")
for k in FORECAST_HORIZONS:
    print(f"\n  {k}-Day Forecast:")
    print(f"    RMSE: {results[k]['val_rmse']:.2f} ft")
    print(f"    MAE:  {results[k]['val_mae']:.2f} ft")
    print(f"    R²:   {results[k]['val_r2']:.3f}")
    print(f"    Features: {len(results[k]['features'])}")
    print(f"    Top: {results[k]['importance'].iloc[0]['feature']}")

print("\n📉 KEY INSIGHTS:")
print(f"  - 1-day forecast: RMSE {results[1]['val_rmse']:.2f} ft (baseline)")
print(f"  - 3-day forecast: RMSE {results[3]['val_rmse']:.2f} ft")
print(f"  - Degradation: +{results[3]['val_rmse'] - results[1]['val_rmse']:.2f} ft over 2 days")

print("\n" + "=" * 70)
print("MULTI-HORIZON FORECAST COMPLETE!")
print("=" * 70)

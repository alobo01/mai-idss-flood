import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import os

print("=" * 70)
print("BASELINE XGBOOST MODEL - WITH OVERPREDICTION BIAS")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Target variable for prediction
TARGET = 'target_level_max'

# Features to EXCLUDE (concurrent values = data leakage!)
EXCLUDE_FEATURES = [
    'date', 'time',
    'target_level_max', 'target_level_mean', 'target_level_min', 'target_level_std',
    'target_level',
    'is_flood', 'is_major_flood',
    'hermann_level', 'grafton_level',  # CONCURRENT upstream
]

# OVERPREDICTION STRATEGIES
OVERPREDICTION_METHODS = {
    'baseline': {
        'description': 'Standard prediction (no bias)',
        'bias': 0.0,
        'quantile': None,
        'asymmetric_weight': 1.0
    },
    'conservative_bias': {
        'description': 'Add +1.5 ft bias (conservative)',
        'bias': 1.5,
        'quantile': None,
        'asymmetric_weight': 1.0
    },
    'quantile_75': {
        'description': 'Predict 75th percentile (upper bound)',
        'bias': 0.0,
        'quantile': 0.75,
        'asymmetric_weight': 1.0
    },
    'quantile_90': {
        'description': 'Predict 90th percentile (very conservative)',
        'bias': 0.0,
        'quantile': 0.90,
        'asymmetric_weight': 1.0
    },
}

# Base hyperparameters (using best from previous run)
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
# 1. LOAD DATA (INCLUDE 3 YEARS FOR VISUALIZATION)
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

# For 3-year visualization: last year of train + val + test
three_years_start = pd.to_datetime('2022-01-01')
train_subset = train_df[train_df['date'] >= three_years_start].copy()
viz_df = pd.concat([train_subset, val_df, test_df], ignore_index=True)
viz_df = viz_df.sort_values('date').reset_index(drop=True)

print(f"\n  Visualization period (3 years):")
print(f"    {viz_df['date'].min().date()} to {viz_df['date'].max().date()}")
print(f"    Total: {len(viz_df)} days")

# =============================================================================
# 2. PREPARE FEATURES
# =============================================================================

print("\n2. Preparing features...")

all_columns = train_df.columns.tolist()
feature_cols = [col for col in all_columns if col not in EXCLUDE_FEATURES]

print(f"  ✓ Total features: {len(feature_cols)}")

X_train = train_df[feature_cols]
y_train = train_df[TARGET]

X_val = val_df[feature_cols]
y_val = val_df[TARGET]

X_viz = viz_df[feature_cols]
y_viz = viz_df[TARGET]

# =============================================================================
# 3. TRAIN MODELS WITH DIFFERENT OVERPREDICTION STRATEGIES
# =============================================================================

print("\n3. Training models with overprediction strategies...")
print("=" * 70)

results = {}

for method_name, config in OVERPREDICTION_METHODS.items():
    print(f"\n{'='*70}")
    print(f"Method: {method_name}")
    print(f"Description: {config['description']}")
    print(f"{'='*70}")
    
    # Configure model based on method
    params = BASE_PARAMS.copy()
    
    if config['quantile'] is not None:
        # Quantile regression
        params['objective'] = 'reg:quantileerror'
        params['quantile_alpha'] = config['quantile']
        print(f"  Using quantile regression: {config['quantile']}")
    
    # Train model
    model = xgb.XGBRegressor(**params)
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    # Predictions (with bias if specified)
    y_pred_val = model.predict(X_val) + config['bias']
    y_pred_viz = model.predict(X_viz) + config['bias']
    
    # Calculate metrics
    val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
    val_mae = mean_absolute_error(y_val, y_pred_val)
    val_r2 = r2_score(y_val, y_pred_val)
    
    # Calculate bias (mean of residuals)
    residuals = y_val.values - y_pred_val
    mean_bias = residuals.mean()  # Negative = overprediction
    
    # Calculate underprediction vs overprediction rates
    underpredictions = (residuals > 0).sum()  # Actual > Predicted (bad for floods!)
    overpredictions = (residuals < 0).sum()   # Actual < Predicted (safe)
    
    print(f"\n  Validation Metrics:")
    print(f"    RMSE: {val_rmse:.2f} ft")
    print(f"    MAE:  {val_mae:.2f} ft")
    print(f"    R²:   {val_r2:.3f}")
    print(f"    Mean bias: {mean_bias:.2f} ft (negative = overpredicting)")
    print(f"    Underpredictions: {underpredictions}/{len(y_val)} ({underpredictions/len(y_val)*100:.1f}%)")
    print(f"    Overpredictions:  {overpredictions}/{len(y_val)} ({overpredictions/len(y_val)*100:.1f}%)")
    
    # Check critical misses (underpredicted floods)
    flood_threshold = 30
    actual_floods = y_val >= flood_threshold
    predicted_floods = y_pred_val >= flood_threshold
    
    missed_floods = (actual_floods & ~predicted_floods).sum()
    false_alarms = (~actual_floods & predicted_floods).sum()
    correct_floods = (actual_floods & predicted_floods).sum()
    
    if actual_floods.sum() > 0:
        print(f"\n  Flood Detection (≥30 ft):")
        print(f"    Actual floods: {actual_floods.sum()}")
        print(f"    Detected: {correct_floods}")
        print(f"    Missed: {missed_floods} ⚠️")
        print(f"    False alarms: {false_alarms}")
    
    # Store results
    results[method_name] = {
        'config': config,
        'model': model,
        'val_rmse': val_rmse,
        'val_mae': val_mae,
        'val_r2': val_r2,
        'mean_bias': mean_bias,
        'underpred_pct': underpredictions/len(y_val)*100,
        'overpred_pct': overpredictions/len(y_val)*100,
        'missed_floods': missed_floods,
        'false_alarms': false_alarms,
        'predictions': {
            'val': y_pred_val,
            'viz': y_pred_viz,
        }
    }

# =============================================================================
# 4. COMPARE METHODS
# =============================================================================

print("\n" + "=" * 70)
print("4. Comparing overprediction strategies...")
print("=" * 70)

comparison_data = []
for method_name, res in results.items():
    comparison_data.append({
        'Method': method_name,
        'Val RMSE': res['val_rmse'],
        'Val MAE': res['val_mae'],
        'Mean Bias': res['mean_bias'],
        'Overpred %': res['overpred_pct'],
        'Missed Floods': res['missed_floods'],
        'False Alarms': res['false_alarms'],
    })

comparison_df = pd.DataFrame(comparison_data)
print("\n" + comparison_df.to_string(index=False))

print("\n💡 Interpretation:")
print("  - Mean Bias < 0 → Model overpredicts (GOOD for safety)")
print("  - Missed Floods → Critical failures (should be minimized)")
print("  - False Alarms → Cost of being conservative")

# =============================================================================
# 5. VISUALIZATIONS
# =============================================================================

print("\n5. Creating visualizations...")
os.makedirs("Results/models", exist_ok=True)

# Plot 1: Comparison metrics
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

methods = comparison_df['Method']

axes[0, 0].bar(methods, comparison_df['Val RMSE'])
axes[0, 0].set_title('Validation RMSE', fontweight='bold', fontsize=11)
axes[0, 0].set_ylabel('RMSE (ft)')
axes[0, 0].tick_params(axis='x', rotation=45)
axes[0, 0].grid(True, alpha=0.3, axis='y')

axes[0, 1].bar(methods, comparison_df['Mean Bias'], color=['green' if x < 0 else 'red' for x in comparison_df['Mean Bias']])
axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=1)
axes[0, 1].set_title('Mean Bias (negative = overpredicting)', fontweight='bold', fontsize=11)
axes[0, 1].set_ylabel('Bias (ft)')
axes[0, 1].tick_params(axis='x', rotation=45)
axes[0, 1].grid(True, alpha=0.3, axis='y')

axes[1, 0].bar(methods, comparison_df['Missed Floods'], color='red', alpha=0.7)
axes[1, 0].set_title('Missed Floods (lower is better)', fontweight='bold', fontsize=11)
axes[1, 0].set_ylabel('Count')
axes[1, 0].tick_params(axis='x', rotation=45)
axes[1, 0].grid(True, alpha=0.3, axis='y')

axes[1, 1].bar(methods, comparison_df['False Alarms'], color='orange', alpha=0.7)
axes[1, 1].set_title('False Alarms (cost of being conservative)', fontweight='bold', fontsize=11)
axes[1, 1].set_ylabel('Count')
axes[1, 1].tick_params(axis='x', rotation=45)
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('Results/models/overprediction_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: overprediction_comparison.png")

# Plot 2: LARGE 3-YEAR TIME SERIES (separate plot for each method)
for method_name, res in results.items():
    fig, ax = plt.subplots(figsize=(20, 8))
    
    viz_dates = viz_df['date'].values
    y_pred_viz = res['predictions']['viz']
    
    ax.plot(viz_dates, y_viz.values, label='Actual', linewidth=2, alpha=0.8, color='blue')
    ax.plot(viz_dates, y_pred_viz, label=f'Predicted ({method_name})', linewidth=2, alpha=0.8, color='red', linestyle='--')
    ax.axhline(y=30, color='orange', linestyle=':', linewidth=2, alpha=0.7, label='Flood Stage (30 ft)')
    ax.axhline(y=40, color='darkred', linestyle=':', linewidth=2, alpha=0.7, label='Major Flood (40 ft)')
    
    # Add vertical lines for train/val/test splits
    ax.axvline(x=pd.to_datetime('2023-01-01'), color='green', linestyle='--', linewidth=2, alpha=0.5, label='Val Start')
    ax.axvline(x=pd.to_datetime('2024-01-01'), color='purple', linestyle='--', linewidth=2, alpha=0.5, label='Test Start')
    
    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('River Level (ft)', fontsize=14, fontweight='bold')
    ax.set_title(f'3-Year Timeline: {method_name}\n{OVERPREDICTION_METHODS[method_name]["description"]}\nMean Bias: {res["mean_bias"]:.2f} ft | Missed Floods: {res["missed_floods"]}', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(f'Results/models/timeseries_3year_{method_name}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: timeseries_3year_{method_name}.png")

# Plot 3: Feature importance (baseline model)
baseline_model = results['baseline']['model']
feature_importance = baseline_model.feature_importances_
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': feature_importance
}).sort_values('importance', ascending=False).head(20)

fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(importance_df['feature'], importance_df['importance'])
ax.set_xlabel('Importance', fontsize=11)
ax.set_title('Top 20 Feature Importances (Baseline Model)', fontsize=12, fontweight='bold')
ax.invert_yaxis()
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('Results/models/feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: feature_importance.png")

# =============================================================================
# 6. SAVE RESULTS
# =============================================================================

print("\n6. Saving results...")

comparison_df.to_csv('Results/models/overprediction_comparison.csv', index=False)
print("  ✓ Saved: overprediction_comparison.csv")

# Save all models
for method_name, res in results.items():
    res['model'].save_model(f'Results/models/model_{method_name}.json')
print(f"  ✓ Saved: {len(results)} models")

# =============================================================================
# 7. SUMMARY AND RECOMMENDATIONS
# =============================================================================

print("\n" + "=" * 70)
print("OVERPREDICTION ANALYSIS SUMMARY")
print("=" * 70)

print(f"\n📊 Methods compared: {len(results)}")
print(f"📊 Validation samples: {len(val_df)}")
print(f"📊 3-year visualization: {len(viz_df)} days")

print("\n🎯 RECOMMENDATIONS:")

# Find safest model (fewest missed floods)
safest = comparison_df.loc[comparison_df['Missed Floods'].idxmin()]
print(f"\n  1. SAFEST (fewest missed floods): {safest['Method']}")
print(f"     - Missed floods: {int(safest['Missed Floods'])}")
print(f"     - Mean bias: {safest['Mean Bias']:.2f} ft")
print(f"     - False alarms: {int(safest['False Alarms'])}")

# Find best accuracy
best_accuracy = comparison_df.loc[comparison_df['Val RMSE'].idxmin()]
print(f"\n  2. BEST ACCURACY: {best_accuracy['Method']}")
print(f"     - RMSE: {best_accuracy['Val RMSE']:.2f} ft")
print(f"     - Missed floods: {int(best_accuracy['Missed Floods'])}")

print("\n💡 For flood early warning systems:")
print("   → Use 'quantile_75' or 'quantile_90' for conservative predictions")
print("   → Accept higher false alarm rate to minimize missed floods")
print("   → Monitor mean bias to ensure consistent overprediction")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)
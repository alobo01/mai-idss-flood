import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

print("=" * 70)
print("TEMPORAL TRAIN/VALIDATION/TEST SPLIT")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Temporal split points (CRITICAL: Must be chronological!)
SPLIT_CONFIG = {
    'train_end': '2022-12-31',      # Train: 2001 to end of 2022
    'val_end': '2023-12-31',        # Validation: All of 2023
    'test_end': '2025-09-08'        # Test: 2024 to Sept 2025
}

print("\nSplit configuration:")
print(f"  Train:      Start → {SPLIT_CONFIG['train_end']}")
print(f"  Validation: {SPLIT_CONFIG['train_end']} → {SPLIT_CONFIG['val_end']}")
print(f"  Test:       {SPLIT_CONFIG['val_end']} → {SPLIT_CONFIG['test_end']}")

# =============================================================================
# 1. PROCESS DAILY DATASET
# =============================================================================

print("\n" + "=" * 70)
print("SPLITTING DAILY DATASET")
print("=" * 70)

print("\n1. Loading daily dataset with lags...")
daily_df = pd.read_csv("Data/processed/daily_flood_dataset_with_lags.csv")
daily_df['date'] = pd.to_datetime(daily_df['date'])

print(f"  ✓ Loaded: {daily_df.shape[0]} days, {daily_df.shape[1]} features")
print(f"  ✓ Date range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}")

# 1.2 Create splits
print("\n2. Creating temporal splits...")

train_end = pd.to_datetime(SPLIT_CONFIG['train_end'])
val_end = pd.to_datetime(SPLIT_CONFIG['val_end'])
test_end = pd.to_datetime(SPLIT_CONFIG['test_end'])

daily_train = daily_df[daily_df['date'] <= train_end].copy()
daily_val = daily_df[(daily_df['date'] > train_end) & (daily_df['date'] <= val_end)].copy()
daily_test = daily_df[(daily_df['date'] > val_end) & (daily_df['date'] <= test_end)].copy()

print(f"\n  Train set:")
print(f"    - {len(daily_train)} days ({len(daily_train)/len(daily_df)*100:.1f}%)")
print(f"    - {daily_train['date'].min().date()} to {daily_train['date'].max().date()}")
print(f"    - Flood days: {daily_train['is_flood'].sum()} ({daily_train['is_flood'].sum()/len(daily_train)*100:.1f}%)")

print(f"\n  Validation set:")
print(f"    - {len(daily_val)} days ({len(daily_val)/len(daily_df)*100:.1f}%)")
print(f"    - {daily_val['date'].min().date()} to {daily_val['date'].max().date()}")
print(f"    - Flood days: {daily_val['is_flood'].sum()} ({daily_val['is_flood'].sum()/len(daily_val)*100:.1f}%)")

print(f"\n  Test set:")
print(f"    - {len(daily_test)} days ({len(daily_test)/len(daily_df)*100:.1f}%)")
print(f"    - {daily_test['date'].min().date()} to {daily_test['date'].max().date()}")
print(f"    - Flood days: {daily_test['is_flood'].sum()} ({daily_test['is_flood'].sum()/len(daily_test)*100:.1f}%)")

# 1.3 Save splits
print("\n3. Saving daily splits...")
output_folder = "Data/processed/"

daily_train.to_csv(output_folder + "daily_train.csv", index=False)
daily_val.to_csv(output_folder + "daily_val.csv", index=False)
daily_test.to_csv(output_folder + "daily_test.csv", index=False)

print(f"  ✓ Saved: daily_train.csv")
print(f"  ✓ Saved: daily_val.csv")
print(f"  ✓ Saved: daily_test.csv")

# =============================================================================
# 2. PROCESS HOURLY DATASET
# =============================================================================

print("\n" + "=" * 70)
print("SPLITTING HOURLY DATASET")
print("=" * 70)

print("\n1. Loading hourly dataset with lags...")
hourly_df = pd.read_csv("Data/processed/hourly_flood_dataset_with_lags.csv")
hourly_df['time'] = pd.to_datetime(hourly_df['time'])

print(f"  ✓ Loaded: {hourly_df.shape[0]} hours, {hourly_df.shape[1]} features")
print(f"  ✓ Date range: {hourly_df['time'].min()} to {hourly_df['time'].max()}")

# 2.2 Create splits
print("\n2. Creating temporal splits...")

hourly_train = hourly_df[hourly_df['time'] <= train_end].copy()
hourly_val = hourly_df[(hourly_df['time'] > train_end) & (hourly_df['time'] <= val_end)].copy()
hourly_test = hourly_df[(hourly_df['time'] > val_end) & (hourly_df['time'] <= test_end)].copy()

print(f"\n  Train set:")
print(f"    - {len(hourly_train)} hours ({len(hourly_train)/len(hourly_df)*100:.1f}%)")
print(f"    - {hourly_train['time'].min()} to {hourly_train['time'].max()}")
print(f"    - Flood hours: {hourly_train['is_flood'].sum()} ({hourly_train['is_flood'].sum()/len(hourly_train)*100:.1f}%)")

print(f"\n  Validation set:")
print(f"    - {len(hourly_val)} hours ({len(hourly_val)/len(hourly_df)*100:.1f}%)")
print(f"    - {hourly_val['time'].min()} to {hourly_val['time'].max()}")
print(f"    - Flood hours: {hourly_val['is_flood'].sum()} ({hourly_val['is_flood'].sum()/len(hourly_val)*100:.1f}%)")

print(f"\n  Test set:")
print(f"    - {len(hourly_test)} hours ({len(hourly_test)/len(hourly_df)*100:.1f}%)")
print(f"    - {hourly_test['time'].min()} to {hourly_test['time'].max()}")
print(f"    - Flood hours: {hourly_test['is_flood'].sum()} ({hourly_test['is_flood'].sum()/len(hourly_test)*100:.1f}%)")

# 2.3 Save splits
print("\n3. Saving hourly splits...")

hourly_train.to_csv(output_folder + "hourly_train.csv", index=False)
hourly_val.to_csv(output_folder + "hourly_val.csv", index=False)
hourly_test.to_csv(output_folder + "hourly_test.csv", index=False)

print(f"  ✓ Saved: hourly_train.csv")
print(f"  ✓ Saved: hourly_val.csv")
print(f"  ✓ Saved: hourly_test.csv")

# =============================================================================
# 3. VISUALIZATION OF SPLITS
# =============================================================================

print("\n4. Creating visualization of splits...")
os.makedirs("Results/data_quality", exist_ok=True)

# Daily visualization
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Plot 1: Full timeline with split boundaries
axes[0].plot(daily_df['date'], daily_df['target_level_max'], linewidth=0.5, alpha=0.7, color='blue')
axes[0].axvline(x=train_end, color='red', linestyle='--', linewidth=2, label='Train/Val split')
axes[0].axvline(x=val_end, color='orange', linestyle='--', linewidth=2, label='Val/Test split')
axes[0].axhline(y=30, color='green', linestyle=':', alpha=0.5, label='Flood stage')
axes[0].set_ylabel('Target Level (ft)', fontsize=11)
axes[0].set_title('Daily Dataset: Temporal Split Visualization', fontsize=12, fontweight='bold')
axes[0].legend(loc='upper left')
axes[0].grid(True, alpha=0.3)

# Add text annotations for splits
axes[0].text(daily_train['date'].mean(), axes[0].get_ylim()[1] * 0.95, 
            'TRAIN', ha='center', fontsize=12, fontweight='bold', 
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
axes[0].text(daily_val['date'].mean(), axes[0].get_ylim()[1] * 0.95, 
            'VAL', ha='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
axes[0].text(daily_test['date'].mean(), axes[0].get_ylim()[1] * 0.95, 
            'TEST', ha='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))

# Plot 2: Distribution comparison
splits = ['Train', 'Val', 'Test']
flood_pcts = [
    daily_train['is_flood'].sum() / len(daily_train) * 100,
    daily_val['is_flood'].sum() / len(daily_val) * 100,
    daily_test['is_flood'].sum() / len(daily_test) * 100
]
mean_levels = [
    daily_train['target_level_max'].mean(),
    daily_val['target_level_max'].mean(),
    daily_test['target_level_max'].mean()
]

ax2 = axes[1]
ax2_twin = ax2.twinx()

bars1 = ax2.bar(np.arange(len(splits)) - 0.2, mean_levels, 0.4, 
               label='Mean Level', color='steelblue')
bars2 = ax2_twin.bar(np.arange(len(splits)) + 0.2, flood_pcts, 0.4, 
                     label='Flood %', color='coral')

ax2.set_ylabel('Mean Target Level (ft)', fontsize=11)
ax2_twin.set_ylabel('Flood Percentage (%)', fontsize=11)
ax2.set_xlabel('Split', fontsize=11)
ax2.set_xticks(np.arange(len(splits)))
ax2.set_xticklabels(splits)
ax2.set_title('Split Characteristics Comparison', fontsize=12, fontweight='bold')
ax2.legend(loc='upper left')
ax2_twin.legend(loc='upper right')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('Results/data_quality/temporal_splits.png', dpi=150, bbox_inches='tight')
plt.close()

print("  ✓ Saved: temporal_splits.png")

# =============================================================================
# 4. SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("TEMPORAL SPLIT SUMMARY")
print("=" * 70)

print("\n📊 DAILY DATASET:")
print(f"  Total: {len(daily_df)} days")
print(f"  Train: {len(daily_train)} days ({len(daily_train)/len(daily_df)*100:.1f}%)")
print(f"  Val:   {len(daily_val)} days ({len(daily_val)/len(daily_df)*100:.1f}%)")
print(f"  Test:  {len(daily_test)} days ({len(daily_test)/len(daily_df)*100:.1f}%)")

print("\n📊 HOURLY DATASET:")
print(f"  Total: {len(hourly_df)} hours")
print(f"  Train: {len(hourly_train)} hours ({len(hourly_train)/len(hourly_df)*100:.1f}%)")
print(f"  Val:   {len(hourly_val)} hours ({len(hourly_val)/len(hourly_df)*100:.1f}%)")
print(f"  Test:  {len(hourly_test)} hours ({len(hourly_test)/len(hourly_df)*100:.1f}%)")

print("\n⚠️  IMPORTANT NOTES:")
print("  1. Splits are TEMPORAL (not random) - preserves time series structure")
print("  2. NO data leakage - test data is in the future")
print("  3. Use validation set for hyperparameter tuning")
print("  4. Test set represents true out-of-sample performance")

print("\n" + "=" * 70)
print("TEMPORAL SPLIT COMPLETE!")
print("=" * 70)

print("\nCreated files:")
print("  Daily splits:")
print("    - Data/processed/daily_train.csv")
print("    - Data/processed/daily_val.csv")
print("    - Data/processed/daily_test.csv")
print("\n  Hourly splits:")
print("    - Data/processed/hourly_train.csv")
print("    - Data/processed/hourly_val.csv")
print("    - Data/processed/hourly_test.csv")

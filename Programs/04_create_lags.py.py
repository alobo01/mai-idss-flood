import pandas as pd
import numpy as np
import os

print("=" * 70)
print("CREATING LAG FEATURES FOR TIME SERIES MODELING")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Lag configurations
DAILY_LAGS = {
    'upstream': [1, 2, 3, 5, 7],  # Days - based on our 1-day optimal lag
    'target': [1, 2, 3],  # Autoregressive lags
    'weather': [1, 3, 7]  # Weather lags
}

HOURLY_LAGS = {
    'upstream': [6, 12, 24, 48, 72],  # Hours
    'target': [6, 12, 24],  # Hours
    'weather': [6, 12, 24]  # Hours
}

# =============================================================================
# 1. PROCESS DAILY DATASET
# =============================================================================

print("\n" + "=" * 70)
print("PROCESSING DAILY DATASET")
print("=" * 70)

print("\n1. Loading daily dataset...")
daily_df = pd.read_csv("Data/processed/daily_flood_dataset.csv")
daily_df['date'] = pd.to_datetime(daily_df['date'])
print(f"  ✓ Loaded: {daily_df.shape[0]} days, {daily_df.shape[1]} features")

print("\n2. Creating lag features...")

# 2.1 Upstream station lags
print(f"\n  Creating upstream lags: {DAILY_LAGS['upstream']} days")
for lag in DAILY_LAGS['upstream']:
    daily_df[f'hermann_level_lag{lag}d'] = daily_df['hermann_level'].shift(lag)
    daily_df[f'grafton_level_lag{lag}d'] = daily_df['grafton_level'].shift(lag)
print(f"    ✓ Created {len(DAILY_LAGS['upstream']) * 2} upstream lag features")

# 2.2 Target autoregressive lags
print(f"\n  Creating target lags: {DAILY_LAGS['target']} days")
for lag in DAILY_LAGS['target']:
    daily_df[f'target_level_max_lag{lag}d'] = daily_df['target_level_max'].shift(lag)
print(f"    ✓ Created {len(DAILY_LAGS['target'])} target lag features")

# 2.3 Weather lags (optional - we already have cumulative features)
print(f"\n  Creating weather lags: {DAILY_LAGS['weather']} days")
for lag in DAILY_LAGS['weather']:
    daily_df[f'daily_precip_lag{lag}d'] = daily_df['daily_precip'].shift(lag)
    daily_df[f'daily_temp_lag{lag}d'] = daily_df['daily_temp_avg'].shift(lag)
print(f"    ✓ Created {len(DAILY_LAGS['weather']) * 2} weather lag features")

# 2.4 Rolling statistics (moving averages for upstream)
print("\n  Creating rolling statistics...")
for window in [3, 7, 14]:
    daily_df[f'hermann_level_ma{window}d'] = daily_df['hermann_level'].rolling(window=window).mean()
    daily_df[f'grafton_level_ma{window}d'] = daily_df['grafton_level'].rolling(window=window).mean()
print(f"    ✓ Created {3 * 2} rolling average features")

# 2.5 Rate of change features
print("\n  Creating rate of change features...")
daily_df['hermann_level_change_1d'] = daily_df['hermann_level'].diff(1)
daily_df['hermann_level_change_3d'] = daily_df['hermann_level'].diff(3)
daily_df['grafton_level_change_1d'] = daily_df['grafton_level'].diff(1)
print("    ✓ Created 3 rate of change features")

print(f"\n  Total features now: {daily_df.shape[1]}")

# 2.6 Handle missing values from lag creation
print("\n3. Handling missing values from lags...")
initial_rows = len(daily_df)

# Drop rows where critical lags are missing (warm-up period)
# Keep rows where at least the 1-day lag exists
max_lag = max(DAILY_LAGS['upstream'])
rows_before = len(daily_df)
daily_df = daily_df.dropna(subset=['hermann_level_lag1d', 'grafton_level_lag1d'])
rows_after = len(daily_df)

print(f"  ✓ Dropped {rows_before - rows_after} initial rows (warm-up period)")
print(f"  ✓ Remaining rows: {rows_after}")

# Fill remaining NaNs (if any) with forward fill
remaining_na = daily_df.isna().sum().sum()
if remaining_na > 0:
    print(f"  Filling {remaining_na} remaining NaN values...")
    daily_df = daily_df.fillna(method='ffill').fillna(method='bfill')

# 2.7 Save
print("\n4. Saving daily dataset with lags...")
output_file = "Data/processed/daily_flood_dataset_with_lags.csv"
daily_df.to_csv(output_file, index=False)
file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"  ✓ Saved: {output_file}")
print(f"  ✓ Shape: {daily_df.shape[0]} days × {daily_df.shape[1]} features")
print(f"  ✓ File size: {file_size_mb:.2f} MB")

# =============================================================================
# 2. PROCESS HOURLY DATASET
# =============================================================================

print("\n" + "=" * 70)
print("PROCESSING HOURLY DATASET")
print("=" * 70)

print("\n1. Loading hourly dataset...")
hourly_df = pd.read_csv("Data/processed/hourly_flood_dataset.csv")
hourly_df['time'] = pd.to_datetime(hourly_df['time'])
print(f"  ✓ Loaded: {hourly_df.shape[0]} hours, {hourly_df.shape[1]} features")

print("\n2. Creating lag features...")

# 2.1 Upstream station lags
print(f"\n  Creating upstream lags: {HOURLY_LAGS['upstream']} hours")
for lag in HOURLY_LAGS['upstream']:
    hourly_df[f'hermann_level_lag{lag}h'] = hourly_df['hermann_level'].shift(lag)
    hourly_df[f'grafton_level_lag{lag}h'] = hourly_df['grafton_level'].shift(lag)
print(f"    ✓ Created {len(HOURLY_LAGS['upstream']) * 2} upstream lag features")

# 2.2 Target autoregressive lags
print(f"\n  Creating target lags: {HOURLY_LAGS['target']} hours")
for lag in HOURLY_LAGS['target']:
    hourly_df[f'target_level_lag{lag}h'] = hourly_df['target_level'].shift(lag)
print(f"    ✓ Created {len(HOURLY_LAGS['target'])} target lag features")

# 2.3 Weather lags
print(f"\n  Creating weather lags: {HOURLY_LAGS['weather']} hours")
for lag in HOURLY_LAGS['weather']:
    hourly_df[f'precipitation_lag{lag}h'] = hourly_df['precipitation'].shift(lag)
    hourly_df[f'temperature_lag{lag}h'] = hourly_df['temperature_2m'].shift(lag)
print(f"    ✓ Created {len(HOURLY_LAGS['weather']) * 2} weather lag features")

# 2.4 Rolling statistics
print("\n  Creating rolling statistics...")
for window in [6, 24, 72]:  # 6h, 1d, 3d
    hourly_df[f'hermann_level_ma{window}h'] = hourly_df['hermann_level'].rolling(window=window).mean()
    hourly_df[f'grafton_level_ma{window}h'] = hourly_df['grafton_level'].rolling(window=window).mean()
print(f"    ✓ Created {3 * 2} rolling average features")

# 2.5 Rate of change features
print("\n  Creating rate of change features...")
hourly_df['hermann_level_change_6h'] = hourly_df['hermann_level'].diff(6)
hourly_df['hermann_level_change_24h'] = hourly_df['hermann_level'].diff(24)
hourly_df['grafton_level_change_6h'] = hourly_df['grafton_level'].diff(6)
print("    ✓ Created 3 rate of change features")

print(f"\n  Total features now: {hourly_df.shape[1]}")

# 2.6 Handle missing values from lag creation
print("\n3. Handling missing values from lags...")

# Drop rows where critical lags are missing
rows_before = len(hourly_df)
hourly_df = hourly_df.dropna(subset=['hermann_level_lag24h', 'grafton_level_lag24h'])
rows_after = len(hourly_df)

print(f"  ✓ Dropped {rows_before - rows_after} initial rows (warm-up period)")
print(f"  ✓ Remaining rows: {rows_after}")

# Fill remaining NaNs
remaining_na = hourly_df.isna().sum().sum()
if remaining_na > 0:
    print(f"  Filling {remaining_na} remaining NaN values...")
    hourly_df = hourly_df.fillna(method='ffill').fillna(method='bfill')

# 2.7 Save
print("\n4. Saving hourly dataset with lags...")
output_file = "Data/processed/hourly_flood_dataset_with_lags.csv"
hourly_df.to_csv(output_file, index=False)
file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"  ✓ Saved: {output_file}")
print(f"  ✓ Shape: {hourly_df.shape[0]} hours × {hourly_df.shape[1]} features")
print(f"  ✓ File size: {file_size_mb:.2f} MB")

# =============================================================================
# 3. SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("LAG FEATURE CREATION SUMMARY")
print("=" * 70)

print("\n📊 DAILY DATASET:")
print(f"  Original features: ~19")
print(f"  New features: {daily_df.shape[1]}")
print(f"  Records: {daily_df.shape[0]} days")
print("\n  Added features:")
print(f"    - Upstream lags: {len(DAILY_LAGS['upstream'])} × 2 stations")
print(f"    - Target lags: {len(DAILY_LAGS['target'])}")
print(f"    - Weather lags: {len(DAILY_LAGS['weather'])} × 2 variables")
print(f"    - Rolling averages: 3 windows × 2 stations")
print(f"    - Rate of change: 3 features")

print("\n📊 HOURLY DATASET:")
print(f"  Original features: ~17")
print(f"  New features: {hourly_df.shape[1]}")
print(f"  Records: {hourly_df.shape[0]} hours")
print("\n  Added features:")
print(f"    - Upstream lags: {len(HOURLY_LAGS['upstream'])} × 2 stations")
print(f"    - Target lags: {len(HOURLY_LAGS['target'])}")
print(f"    - Weather lags: {len(HOURLY_LAGS['weather'])} × 2 variables")
print(f"    - Rolling averages: 3 windows × 2 stations")
print(f"    - Rate of change: 3 features")

print("\n" + "=" * 70)
print("LAG FEATURE CREATION COMPLETE!")
print("=" * 70)

print("\nCreated files:")
print("  1. Data/processed/daily_flood_dataset_with_lags.csv")
print("  2. Data/processed/hourly_flood_dataset_with_lags.csv")


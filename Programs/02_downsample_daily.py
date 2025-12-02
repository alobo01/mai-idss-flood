import pandas as pd
import numpy as np
import os

print("=" * 70)
print("CREATING DAILY DATASET FOR FLOOD PREDICTION")
print("=" * 70)

# =============================================================================
# 1. LOAD DATA
# =============================================================================

print("\n1. Loading data...")
folder = "Data/datasets/"

river_target_st_louis = pd.read_csv(folder + "river_target_st_louis.csv")
river_upstream_grafton = pd.read_csv(folder + "river_upstream_grafton.csv")
river_upstream_hermann = pd.read_csv(folder + "river_upstream_hermann.csv")
weather_history_st_louis = pd.read_csv(folder + "weather_history_st_louis.csv.gz", compression="gzip")

# Parse dates
river_target_st_louis['time'] = pd.to_datetime(river_target_st_louis['time']).dt.tz_localize(None)
river_upstream_grafton['time'] = pd.to_datetime(river_upstream_grafton['time']).dt.tz_localize(None)
river_upstream_hermann['time'] = pd.to_datetime(river_upstream_hermann['time']).dt.tz_localize(None)
weather_history_st_louis['datetime'] = pd.to_datetime(weather_history_st_louis['datetime'])

print("  ✓ Data loaded")

# =============================================================================
# 2. FILTER TO COMMON DATE RANGE
# =============================================================================

print("\n2. Filtering to common date range...")

common_start = pd.to_datetime('2001-10-04')
common_end = pd.to_datetime('2025-09-08')

river_target_st_louis = river_target_st_louis[
    (river_target_st_louis['time'] >= common_start) & 
    (river_target_st_louis['time'] <= common_end)
].copy()

river_upstream_grafton = river_upstream_grafton[
    (river_upstream_grafton['time'] >= common_start) & 
    (river_upstream_grafton['time'] <= common_end)
].copy()

river_upstream_hermann = river_upstream_hermann[
    (river_upstream_hermann['time'] >= common_start) & 
    (river_upstream_hermann['time'] <= common_end)
].copy()

weather_history_st_louis = weather_history_st_louis[
    (weather_history_st_louis['datetime'] >= common_start) & 
    (weather_history_st_louis['datetime'] <= common_end)
].copy()

print(f"  ✓ Date range: {common_start.date()} to {common_end.date()}")

# =============================================================================
# 3. DOWNSAMPLE TARGET TO DAILY
# =============================================================================

print("\n3. Downsampling target (St. Louis) to daily...")

# Create date column
river_target_st_louis['date'] = river_target_st_louis['time'].dt.date

# Aggregate to daily - use MAX for flood prediction (captures peak levels)
target_daily = river_target_st_louis.groupby('date').agg({
    'usgs_level': ['max', 'mean', 'min', 'std']
}).reset_index()

# Flatten column names
target_daily.columns = ['date', 'target_level_max', 'target_level_mean', 'target_level_min', 'target_level_std']
target_daily['date'] = pd.to_datetime(target_daily['date'])

print(f"  ✓ Target downsampled: {len(target_daily)} days")
print(f"    - Max level range: {target_daily['target_level_max'].min():.1f} to {target_daily['target_level_max'].max():.1f} ft")

# =============================================================================
# 4. PREPARE UPSTREAM STATIONS (ALREADY DAILY)
# =============================================================================

print("\n4. Preparing upstream stations (already daily)...")

# Grafton
grafton_daily = river_upstream_grafton.copy()
grafton_daily['date'] = pd.to_datetime(grafton_daily['time'].dt.date)
grafton_daily = grafton_daily[['date', 'grafton_level']].copy()

# Hermann
hermann_daily = river_upstream_hermann.copy()
hermann_daily['date'] = pd.to_datetime(hermann_daily['time'].dt.date)
hermann_daily = hermann_daily[['date', 'hermann_level']].copy()

print(f"  ✓ Grafton: {len(grafton_daily)} days, {grafton_daily['grafton_level'].isna().sum()} missing")
print(f"  ✓ Hermann: {len(hermann_daily)} days, {hermann_daily['hermann_level'].isna().sum()} missing")

# =============================================================================
# 5. CREATE WEATHER FEATURES (DAILY)
# =============================================================================

print("\n5. Creating weather features...")

# First, merge weather at hourly level, then create features
weather_history_st_louis = weather_history_st_louis.sort_values('datetime').reset_index(drop=True)

# Create lagged cumulative precipitation features (at hourly level)
# Use 12h lag as representative (from our analysis)
windows = [168, 336, 720]  # 7-day, 14-day, 30-day

for window in windows:
    feature_name = f'precip_{window}h'
    weather_history_st_louis[feature_name] = (
        weather_history_st_louis['precipitation']
        .shift(12)  # 12h lag
        .rolling(window=window, min_periods=1)
        .sum()
    )

# Deep soil moisture (30-day average, 12h lag)
weather_history_st_louis['soil_deep_720h'] = (
    weather_history_st_louis['soil_moisture_28_to_100cm']
    .shift(12)
    .rolling(window=720, min_periods=1)
    .mean()
)

# Heavy rain indicator (>15mm in last 48h)
weather_history_st_louis['precip_48h'] = (
    weather_history_st_louis['precipitation']
    .rolling(window=48, min_periods=1)
    .sum()
)
weather_history_st_louis['heavy_rain_48h'] = (
    weather_history_st_louis['precip_48h'] > 15
).astype(int)

# Now downsample weather to daily
weather_history_st_louis['date'] = pd.to_datetime(weather_history_st_louis['datetime'].dt.date)

weather_daily = weather_history_st_louis.groupby('date').agg({
    'precipitation': 'sum',  # Daily total
    'temperature_2m': 'mean',  # Daily average
    'snowfall': 'sum',  # Daily total
    'relative_humidity_2m': 'mean',
    'wind_speed_10m': 'mean',
    'precip_168h': 'mean',  # Average of hourly calculations
    'precip_336h': 'mean',
    'precip_720h': 'mean',
    'soil_deep_720h': 'mean',
    'heavy_rain_48h': 'max'  # If any hour had heavy rain, mark the day
}).reset_index()

# Rename for clarity
weather_daily = weather_daily.rename(columns={
    'precipitation': 'daily_precip',
    'temperature_2m': 'daily_temp_avg',
    'snowfall': 'daily_snowfall',
    'relative_humidity_2m': 'daily_humidity',
    'wind_speed_10m': 'daily_wind',
    'precip_168h': 'precip_7d',
    'precip_336h': 'precip_14d',
    'precip_720h': 'precip_30d',
    'soil_deep_720h': 'soil_deep_30d'
})

print(f"  ✓ Weather downsampled: {len(weather_daily)} days")
print(f"    - Features created: 7d/14d/30d precip, deep soil, heavy rain indicator")

# =============================================================================
# 6. MERGE ALL DATA
# =============================================================================

print("\n6. Merging all datasets...")

# Start with target
daily_dataset = target_daily.copy()

# Merge upstream stations
daily_dataset = daily_dataset.merge(grafton_daily, on='date', how='left')
daily_dataset = daily_dataset.merge(hermann_daily, on='date', how='left')

# Merge weather
daily_dataset = daily_dataset.merge(weather_daily, on='date', how='left')

# Sort by date
daily_dataset = daily_dataset.sort_values('date').reset_index(drop=True)

print(f"  ✓ Merged dataset: {len(daily_dataset)} days, {daily_dataset.shape[1]} features")

# =============================================================================
# 7. CREATE FLOOD INDICATORS
# =============================================================================

print("\n7. Creating flood indicators...")

FLOOD_STAGE = 30
MAJOR_FLOOD = 40

daily_dataset['is_flood'] = (daily_dataset['target_level_max'] >= FLOOD_STAGE).astype(int)
daily_dataset['is_major_flood'] = (daily_dataset['target_level_max'] >= MAJOR_FLOOD).astype(int)

flood_days = daily_dataset['is_flood'].sum()
major_flood_days = daily_dataset['is_major_flood'].sum()

print(f"  ✓ Flood days (≥30 ft): {flood_days} ({flood_days/len(daily_dataset)*100:.1f}%)")
print(f"  ✓ Major flood days (≥40 ft): {major_flood_days} ({major_flood_days/len(daily_dataset)*100:.1f}%)")

# =============================================================================
# 8. DATA QUALITY CHECK
# =============================================================================

print("\n8. Data quality check...")

missing_summary = daily_dataset.isna().sum()
missing_summary = missing_summary[missing_summary > 0].sort_values(ascending=False)

if len(missing_summary) > 0:
    print("\n  Missing values:")
    for col, count in missing_summary.items():
        pct = count / len(daily_dataset) * 100
        print(f"    - {col}: {count} ({pct:.2f}%)")
else:
    print("  ✓ No missing values!")


# =============================================================================
# 8B. IMPUTE MISSING VALUES
# =============================================================================

print("\n8b. Imputing missing values...")

# For upstream river levels: use linear interpolation (river changes gradually)
if daily_dataset['grafton_level'].isna().sum() > 0:
    before = daily_dataset['grafton_level'].isna().sum()
    daily_dataset['grafton_level'] = daily_dataset['grafton_level'].interpolate(method='linear', limit_direction='both')
    print(f"  ✓ Grafton: Interpolated {before} missing values")

if daily_dataset['hermann_level'].isna().sum() > 0:
    before = daily_dataset['hermann_level'].isna().sum()
    daily_dataset['hermann_level'] = daily_dataset['hermann_level'].interpolate(method='linear', limit_direction='both')
    print(f"  ✓ Hermann: Interpolated {before} missing values")

# For target_level_std: fill with 0 (means only 1 measurement that day, so no variation)
if daily_dataset['target_level_std'].isna().sum() > 0:
    before = daily_dataset['target_level_std'].isna().sum()
    daily_dataset['target_level_std'] = daily_dataset['target_level_std'].fillna(0)
    print(f"  ✓ Target std: Filled {before} missing values with 0")

# Verify no missing values remain
remaining_missing = daily_dataset.isna().sum().sum()
if remaining_missing == 0:
    print(f"  ✓ All missing values handled! Dataset is complete.")
else:
    print(f"  ⚠ Warning: {remaining_missing} missing values remain")
    print(daily_dataset.isna().sum()[daily_dataset.isna().sum() > 0])

# =============================================================================
# 9. SAVE DATASET
# =============================================================================

print("\n9. Saving dataset...")

output_folder = "Data/processed/"
os.makedirs(output_folder, exist_ok=True)

output_file = output_folder + "daily_flood_dataset.csv"
daily_dataset.to_csv(output_file, index=False)

file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"  ✓ Saved: {output_file}")
print(f"  ✓ File size: {file_size_mb:.2f} MB")

# =============================================================================
# 10. DATASET SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print(f"\nShape: {daily_dataset.shape[0]} days × {daily_dataset.shape[1]} features")
print(f"Date range: {daily_dataset['date'].min().date()} to {daily_dataset['date'].max().date()}")
print(f"Duration: {(daily_dataset['date'].max() - daily_dataset['date'].min()).days} days")

print("\nFeatures:")
print("  Target variables:")
print("    - target_level_max, target_level_mean, target_level_min, target_level_std")
print("    - is_flood, is_major_flood")
print("\n  Upstream predictors:")
print("    - grafton_level, hermann_level")
print("\n  Weather predictors:")
print("    - daily_precip, daily_temp_avg, daily_snowfall")
print("    - precip_7d, precip_14d, precip_30d (cumulative)")
print("    - soil_deep_30d (deep soil moisture)")
print("    - heavy_rain_48h (binary indicator)")
print("    - daily_humidity, daily_wind")

print("\nTarget statistics:")
print(f"  Max level range: {daily_dataset['target_level_max'].min():.1f} - {daily_dataset['target_level_max'].max():.1f} ft")
print(f"  Mean level: {daily_dataset['target_level_max'].mean():.1f} ft")
print(f"  Std deviation: {daily_dataset['target_level_max'].std():.1f} ft")

# =============================================================================
# 11. SANITY CHECK PLOTS
# =============================================================================

print("\n11. Creating sanity check plots...")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

os.makedirs("Results/data_quality", exist_ok=True)

# Plot 1: All river levels over time
fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)

axes[0].plot(daily_dataset['date'], daily_dataset['target_level_max'], linewidth=0.8, color='blue')
axes[0].axhline(y=30, color='orange', linestyle='--', label='Flood Stage', alpha=0.7)
axes[0].axhline(y=40, color='red', linestyle='--', label='Major Flood', alpha=0.7)
axes[0].set_ylabel('Level (ft)', fontsize=10)
axes[0].set_title('Target: St Louis (Daily Max)', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(daily_dataset['date'], daily_dataset['grafton_level'], linewidth=0.8, color='orange')
axes[1].set_ylabel('Level (ft)', fontsize=10)
axes[1].set_title('Upstream: Grafton (Daily)', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

axes[2].plot(daily_dataset['date'], daily_dataset['hermann_level'], linewidth=0.8, color='green')
axes[2].set_ylabel('Level (ft)', fontsize=10)
axes[2].set_title('Upstream: Hermann (Daily)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Date', fontsize=10)
axes[2].grid(True, alpha=0.3)

# Format x-axis
axes[2].xaxis.set_major_locator(mdates.YearLocator(2))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.setp(axes[2].xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('Results/data_quality/daily_dataset_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: daily_dataset_timeseries.png")

# Plot 2: Correlation check
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].scatter(daily_dataset['hermann_level'], daily_dataset['target_level_max'], 
                alpha=0.3, s=5)
axes[0].set_xlabel('Hermann Level (ft)', fontsize=11)
axes[0].set_ylabel('Target Level Max (ft)', fontsize=11)
axes[0].set_title('Hermann vs Target', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3)

axes[1].scatter(daily_dataset['grafton_level'], daily_dataset['target_level_max'], 
                alpha=0.3, s=5)
axes[1].set_xlabel('Grafton Level (ft)', fontsize=11)
axes[1].set_ylabel('Target Level Max (ft)', fontsize=11)
axes[1].set_title('Grafton vs Target', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Results/data_quality/daily_dataset_correlations.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: daily_dataset_correlations.png")

# Plot 3: Distribution check
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0,0].hist(daily_dataset['target_level_max'], bins=50, edgecolor='black')
axes[0,0].axvline(x=30, color='orange', linestyle='--', label='Flood Stage')
axes[0,0].axvline(x=40, color='red', linestyle='--', label='Major Flood')
axes[0,0].set_xlabel('Target Level (ft)')
axes[0,0].set_ylabel('Count')
axes[0,0].set_title('Target Level Distribution')
axes[0,0].legend()
axes[0,0].grid(True, alpha=0.3)

axes[0,1].hist(daily_dataset['hermann_level'].dropna(), bins=50, edgecolor='black', color='green')
axes[0,1].set_xlabel('Hermann Level (ft)')
axes[0,1].set_ylabel('Count')
axes[0,1].set_title('Hermann Level Distribution')
axes[0,1].grid(True, alpha=0.3)

axes[1,0].hist(daily_dataset['grafton_level'].dropna(), bins=50, edgecolor='black', color='orange')
axes[1,0].set_xlabel('Grafton Level (ft)')
axes[1,0].set_ylabel('Count')
axes[1,0].set_title('Grafton Level Distribution')
axes[1,0].grid(True, alpha=0.3)

axes[1,1].hist(daily_dataset['precip_30d'].dropna(), bins=50, edgecolor='black', color='steelblue')
axes[1,1].set_xlabel('30-day Cumulative Precip (mm)')
axes[1,1].set_ylabel('Count')
axes[1,1].set_title('30-Day Precipitation Distribution')
axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Results/data_quality/daily_dataset_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: daily_dataset_distributions.png")

print("\n✓ All sanity check plots saved to Results/data_quality/")
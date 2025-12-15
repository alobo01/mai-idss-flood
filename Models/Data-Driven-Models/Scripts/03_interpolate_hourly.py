import pandas as pd
import numpy as np
import os

print("=" * 70)
print("CREATING HOURLY INTERPOLATED DATASET FOR FLOOD PREDICTION")
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
print(f"  ✓ Target (hourly): {len(river_target_st_louis)} records")
print(f"  ✓ Upstream (daily): {len(river_upstream_grafton)} / {len(river_upstream_hermann)} records")

# =============================================================================
# 3. INTERPOLATE UPSTREAM STATIONS TO HOURLY
# =============================================================================

print("\n3. Interpolating upstream stations from daily to hourly (polynomial)...")

# Create hourly datetime range
hourly_range = pd.date_range(start=common_start, end=common_end, freq='H')
hourly_df = pd.DataFrame({'time': hourly_range})

# Grafton - polynomial interpolation
print("  Processing Grafton...")
# First, handle missing values in daily data with linear interpolation
river_upstream_grafton['grafton_level'] = river_upstream_grafton['grafton_level'].interpolate(
    method='linear', limit_direction='both'
)

# Merge with hourly range
grafton_hourly = hourly_df.merge(
    river_upstream_grafton[['time', 'grafton_level']],
    on='time',
    how='left'
)

# Polynomial interpolation (order 2 = quadratic)
grafton_hourly['grafton_level'] = grafton_hourly['grafton_level'].interpolate(
    method='polynomial',
    order=2,
    limit_direction='both'
)

print(f"    ✓ Grafton: {len(grafton_hourly)} hourly records created")

# Hermann - polynomial interpolation
print("  Processing Hermann...")
river_upstream_hermann['hermann_level'] = river_upstream_hermann['hermann_level'].interpolate(
    method='linear', limit_direction='both'
)

hermann_hourly = hourly_df.merge(
    river_upstream_hermann[['time', 'hermann_level']],
    on='time',
    how='left'
)

hermann_hourly['hermann_level'] = hermann_hourly['hermann_level'].interpolate(
    method='polynomial',
    order=2,
    limit_direction='both'
)

print(f"    ✓ Hermann: {len(hermann_hourly)} hourly records created")

# =============================================================================
# 4. PREPARE TARGET (ALREADY HOURLY)
# =============================================================================

print("\n4. Preparing target station (already hourly)...")

target_hourly = river_target_st_louis[['time', 'usgs_level']].copy()
target_hourly = target_hourly.rename(columns={'usgs_level': 'target_level'})

print(f"  ✓ Target: {len(target_hourly)} records")

# =============================================================================
# 5. CREATE WEATHER FEATURES (HOURLY)
# =============================================================================

print("\n5. Creating weather features (hourly)...")

# Sort weather data
weather_history_st_louis = weather_history_st_louis.sort_values('datetime').reset_index(drop=True)

# Create lagged cumulative precipitation features
# Use 12h lag as representative
windows = [168, 336, 720]  # 7-day, 14-day, 30-day

for window in windows:
    feature_name = f'precip_{window}h'
    weather_history_st_louis[feature_name] = (
        weather_history_st_louis['precipitation']
        .shift(12)
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

# Select relevant weather columns
weather_hourly = weather_history_st_louis[[
    'datetime', 'precipitation', 'temperature_2m', 'snowfall',
    'relative_humidity_2m', 'wind_speed_10m',
    'precip_168h', 'precip_336h', 'precip_720h',
    'soil_deep_720h', 'heavy_rain_48h'
]].copy()

weather_hourly = weather_hourly.rename(columns={
    'datetime': 'time',
    'precip_168h': 'precip_7d',
    'precip_336h': 'precip_14d',
    'precip_720h': 'precip_30d',
    'soil_deep_720h': 'soil_deep_30d'
})

print(f"  ✓ Weather features: {len(weather_hourly)} records")
print(f"    - Cumulative precip: 7d, 14d, 30d")
print(f"    - Deep soil moisture: 30d average")
print(f"    - Heavy rain indicator")

# =============================================================================
# 6. MERGE ALL DATA
# =============================================================================

print("\n6. Merging all datasets...")

# Start with hourly range to ensure complete coverage
hourly_dataset = hourly_df.copy()

# Merge target
hourly_dataset = hourly_dataset.merge(target_hourly, on='time', how='left')

# Merge upstream (interpolated)
hourly_dataset = hourly_dataset.merge(
    grafton_hourly[['time', 'grafton_level']],
    on='time',
    how='left'
)
hourly_dataset = hourly_dataset.merge(
    hermann_hourly[['time', 'hermann_level']],
    on='time',
    how='left'
)

# Merge weather
hourly_dataset = hourly_dataset.merge(weather_hourly, on='time', how='left')

# Sort by time
hourly_dataset = hourly_dataset.sort_values('time').reset_index(drop=True)

print(f"  ✓ Merged dataset: {len(hourly_dataset)} hours, {hourly_dataset.shape[1]} features")

# =============================================================================
# 7. CREATE FLOOD INDICATORS
# =============================================================================

print("\n7. Creating flood indicators...")

FLOOD_STAGE = 30
MAJOR_FLOOD = 40

hourly_dataset['is_flood'] = (hourly_dataset['target_level'] >= FLOOD_STAGE).astype(int)
hourly_dataset['is_major_flood'] = (hourly_dataset['target_level'] >= MAJOR_FLOOD).astype(int)

flood_hours = hourly_dataset['is_flood'].sum()
major_flood_hours = hourly_dataset['is_major_flood'].sum()

print(f"  ✓ Flood hours (≥30 ft): {flood_hours} ({flood_hours / len(hourly_dataset) * 100:.1f}%)")
print(f"  ✓ Major flood hours (≥40 ft): {major_flood_hours} ({major_flood_hours / len(hourly_dataset) * 100:.1f}%)")

# =============================================================================
# 8. DATA QUALITY CHECK & IMPUTATION
# =============================================================================

print("\n8. Data quality check...")

missing_summary = hourly_dataset.isna().sum()
missing_summary = missing_summary[missing_summary > 0].sort_values(ascending=False)

if len(missing_summary) > 0:
    print("\n  Missing values before imputation:")
    for col, count in missing_summary.items():
        pct = count / len(hourly_dataset) * 100
        print(f"    - {col}: {count} ({pct:.2f}%)")

    print("\n  Imputing missing values...")

    # Fill any remaining NaNs with forward fill then backward fill
    for col in missing_summary.index:
        if col in hourly_dataset.columns:
            hourly_dataset[col] = hourly_dataset[col].fillna(method='ffill').fillna(method='bfill')

    remaining = hourly_dataset.isna().sum().sum()
    if remaining == 0:
        print("  ✓ All missing values handled!")
    else:
        print(f"  ⚠ Warning: {remaining} missing values remain")
else:
    print("  ✓ No missing values!")

# =============================================================================
# 9. SAVE DATASET
# =============================================================================

print("\n9. Saving dataset...")

output_folder = "Data/processed/"
os.makedirs(output_folder, exist_ok=True)

output_file = output_folder + "hourly_flood_dataset.csv"
hourly_dataset.to_csv(output_file, index=False)

file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"  ✓ Saved: {output_file}")
print(f"  ✓ File size: {file_size_mb:.2f} MB")

# =============================================================================
# 10. DATASET SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print(f"\nShape: {hourly_dataset.shape[0]} hours × {hourly_dataset.shape[1]} features")
print(f"Date range: {hourly_dataset['time'].min()} to {hourly_dataset['time'].max()}")
print(f"Duration: {(hourly_dataset['time'].max() - hourly_dataset['time'].min()).days} days")

print("\nFeatures:")
print("  Target variables:")
print("    - target_level, is_flood, is_major_flood")
print("\n  Upstream predictors (polynomial interpolated):")
print("    - grafton_level, hermann_level")
print("\n  Weather predictors:")
print("    - precipitation, temperature_2m, snowfall")
print("    - precip_7d, precip_14d, precip_30d (cumulative)")
print("    - soil_deep_30d (deep soil moisture)")
print("    - heavy_rain_48h (binary indicator)")
print("    - relative_humidity_2m, wind_speed_10m")

print("\nTarget statistics:")
print(f"  Level range: {hourly_dataset['target_level'].min():.1f} - {hourly_dataset['target_level'].max():.1f} ft")
print(f"  Mean level: {hourly_dataset['target_level'].mean():.1f} ft")
print(f"  Std deviation: {hourly_dataset['target_level'].std():.1f} ft")
# =============================================================================
# 11. SANITY CHECK PLOTS (INCLUDING INTERPOLATION QUALITY)
# =============================================================================

print("\n11. Creating sanity check plots...")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

os.makedirs("Models/Data-Driven-Models/Results/data_quality", exist_ok=True)

# Plot 1: Zoom in to see interpolation quality (pick a 2-week period)
sample_start = pd.to_datetime('2008-06-01')
sample_end = pd.to_datetime('2008-06-14')

sample_data = hourly_dataset[
    (hourly_dataset['time'] >= sample_start) &
    (hourly_dataset['time'] <= sample_end)
    ]

# Get original daily data points for comparison
sample_daily_grafton = river_upstream_grafton[
    (river_upstream_grafton['time'] >= sample_start) &
    (river_upstream_grafton['time'] <= sample_end)
    ]
sample_daily_hermann = river_upstream_hermann[
    (river_upstream_hermann['time'] >= sample_start) &
    (river_upstream_hermann['time'] <= sample_end)
    ]

fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Grafton interpolation
axes[0].plot(sample_data['time'], sample_data['grafton_level'],
             linewidth=1.5, color='orange', alpha=0.7, label='Interpolated (hourly)')
axes[0].scatter(sample_daily_grafton['time'], sample_daily_grafton['grafton_level'],
                color='darkred', s=50, zorder=5, label='Original (daily)', marker='o')
axes[0].set_ylabel('Grafton Level (ft)', fontsize=10)
axes[0].set_title('Grafton: Polynomial Interpolation Quality Check', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Hermann interpolation
axes[1].plot(sample_data['time'], sample_data['hermann_level'],
             linewidth=1.5, color='green', alpha=0.7, label='Interpolated (hourly)')
axes[1].scatter(sample_daily_hermann['time'], sample_daily_hermann['hermann_level'],
                color='darkgreen', s=50, zorder=5, label='Original (daily)', marker='o')
axes[1].set_ylabel('Hermann Level (ft)', fontsize=10)
axes[1].set_title('Hermann: Polynomial Interpolation Quality Check', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Date', fontsize=10)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/data_quality/hourly_interpolation_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: hourly_interpolation_quality.png")

# Plot 2: Full time series
fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)

axes[0].plot(hourly_dataset['time'], hourly_dataset['target_level'],
             linewidth=0.3, alpha=0.7, color='blue')
axes[0].axhline(y=30, color='orange', linestyle='--', label='Flood Stage', alpha=0.7)
axes[0].axhline(y=40, color='red', linestyle='--', label='Major Flood', alpha=0.7)
axes[0].set_ylabel('Level (ft)', fontsize=10)
axes[0].set_title('Target: St Louis (Hourly)', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(hourly_dataset['time'], hourly_dataset['grafton_level'],
             linewidth=0.3, alpha=0.7, color='orange')
axes[1].set_ylabel('Level (ft)', fontsize=10)
axes[1].set_title('Upstream: Grafton (Interpolated Hourly)', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

axes[2].plot(hourly_dataset['time'], hourly_dataset['hermann_level'],
             linewidth=0.3, alpha=0.7, color='green')
axes[2].set_ylabel('Level (ft)', fontsize=10)
axes[2].set_title('Upstream: Hermann (Interpolated Hourly)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Date', fontsize=10)
axes[2].grid(True, alpha=0.3)

axes[2].xaxis.set_major_locator(mdates.YearLocator(2))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.setp(axes[2].xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/data_quality/hourly_dataset_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: hourly_dataset_timeseries.png")

# Plot 3: Distribution check
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].hist(hourly_dataset['target_level'].dropna(), bins=100, edgecolor='black')
axes[0, 0].axvline(x=30, color='orange', linestyle='--', label='Flood Stage')
axes[0, 0].axvline(x=40, color='red', linestyle='--', label='Major Flood')
axes[0, 0].set_xlabel('Target Level (ft)')
axes[0, 0].set_ylabel('Count')
axes[0, 0].set_title('Target Level Distribution')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].hist(hourly_dataset['hermann_level'].dropna(), bins=100, edgecolor='black', color='green')
axes[0, 1].set_xlabel('Hermann Level (ft)')
axes[0, 1].set_ylabel('Count')
axes[0, 1].set_title('Hermann Level Distribution (Interpolated)')
axes[0, 1].grid(True, alpha=0.3)

axes[1, 0].hist(hourly_dataset['grafton_level'].dropna(), bins=100, edgecolor='black', color='orange')
axes[1, 0].set_xlabel('Grafton Level (ft)')
axes[1, 0].set_ylabel('Count')
axes[1, 0].set_title('Grafton Level Distribution (Interpolated)')
axes[1, 0].grid(True, alpha=0.3)

axes[1, 1].hist(hourly_dataset['precip_30d'].dropna(), bins=100, edgecolor='black', color='steelblue')
axes[1, 1].set_xlabel('30-day Cumulative Precip (mm)')
axes[1, 1].set_ylabel('Count')
axes[1, 1].set_title('30-Day Precipitation Distribution')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Models/Data-Driven-Models/Results/data_quality/hourly_dataset_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Saved: hourly_dataset_distributions.png")

print("\n✓ All sanity check plots saved to ./Results/data_quality/")
print("\n" + "=" * 70)
print("HOURLY DATASET CREATION COMPLETE!")
print("=" * 70)
print("\nYou now have TWO datasets:")
print("  1. Data/processed/daily_flood_dataset.csv (8,649 days)")
print("  2. Data/processed/hourly_flood_dataset.csv (~210,000 hours)")
print("\nNext: Use either dataset for modeling based on your prediction granularity needs")
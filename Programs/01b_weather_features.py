import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# =============================================================================
# 1. DATA LOADING
# =============================================================================

print("Loading data...")
folder = "Data/datasets/"

river_target_st_louis = pd.read_csv(folder + "river_target_st_louis.csv")
weather_history_st_louis = pd.read_csv(folder + "weather_history_st_louis.csv.gz", compression="gzip")

# Parse dates
river_target_st_louis['time'] = pd.to_datetime(river_target_st_louis['time']).dt.tz_localize(None)
weather_history_st_louis['datetime'] = pd.to_datetime(weather_history_st_louis['datetime'])

# Filter to common period (2001-10-04 to 2025-09-08)
common_start = pd.to_datetime('2001-10-04')
common_end = pd.to_datetime('2025-09-08')

river_target_st_louis = river_target_st_louis[
    (river_target_st_louis['time'] >= common_start) & 
    (river_target_st_louis['time'] <= common_end)
].copy()

weather_history_st_louis = weather_history_st_louis[
    (weather_history_st_louis['datetime'] >= common_start) & 
    (weather_history_st_louis['datetime'] <= common_end)
].copy()

print(f"Target data: {len(river_target_st_louis)} records")
print(f"Weather data: {len(weather_history_st_louis)} records")

# =============================================================================
# 2. MERGE DATASETS ON HOUR
# =============================================================================

print("\nMerging datasets...")
# Merge on datetime
merged = river_target_st_louis.merge(
    weather_history_st_louis,
    left_on='time',
    right_on='datetime',
    how='inner'
)

print(f"Merged data: {len(merged)} records")

# =============================================================================
# 3. CREATE LAGGED PRECIPITATION FEATURES (EXTENDED)
# =============================================================================

print("\nCreating lagged precipitation features (extended windows)...")

# Sort by time
merged = merged.sort_values('time').reset_index(drop=True)

# Define lags (hours before) and windows (cumulative hours)
lags = [3, 6, 12, 24]  # Hours before prediction
windows = [24, 48, 72, 96, 120, 168, 240, 336, 504, 720]  # Up to 30 days (720 hours)

# Calculate lagged cumulative precipitation
for lag in lags:
    for window in windows:
        feature_name = f'precip_lag{lag}h_window{window}h'
        
        # Roll back by lag, then sum over window
        merged[feature_name] = (
            merged['precipitation']
            .shift(lag)  # Shift back by lag hours
            .rolling(window=window, min_periods=1)  # Rolling sum
            .sum()
        )
        
print(f"Created {len(lags) * len(windows)} precipitation features")

# =============================================================================
# 3B. CREATE SOIL MOISTURE FEATURES (SELECTED WINDOWS ONLY)
# =============================================================================

print("\nCreating soil moisture features...")

# Only test windows that worked well for precipitation: 168h, 240h, 336h, 504h, 720h
soil_windows = [168, 240, 336, 504, 720]
soil_lags = [12, 24]  # Just 2 lags to keep it manageable

# We have 3 soil moisture depths
soil_vars = ['soil_moisture_0_to_7cm', 'soil_moisture_7_to_28cm', 'soil_moisture_28_to_100cm']

for soil_var in soil_vars:
    for lag in soil_lags:
        for window in soil_windows:
            feature_name = f'{soil_var}_lag{lag}h_window{window}h'
            
            # Mean soil moisture over window (not sum!)
            merged[feature_name] = (
                merged[soil_var]
                .shift(lag)
                .rolling(window=window, min_periods=1)
                .mean()
            )

print(f"Created {len(soil_vars) * len(soil_lags) * len(soil_windows)} soil moisture features")

# =============================================================================
# 4. CREATE HEAVY RAIN INDICATOR
# =============================================================================

print("\nCreating heavy rain indicator...")

# Heavy rain = more than 15mm in last 48 hours
HEAVY_RAIN_THRESHOLD = 15  # mm

merged['precip_48h'] = merged['precipitation'].rolling(window=48, min_periods=1).sum()
merged['heavy_rain_48h'] = (merged['precip_48h'] > HEAVY_RAIN_THRESHOLD).astype(int)

print(f"Heavy rain events: {merged['heavy_rain_48h'].sum()} hours ({merged['heavy_rain_48h'].sum()/len(merged)*100:.2f}%)")

# =============================================================================
# 5. SNOWMELT ANALYSIS
# =============================================================================

print("\nAnalyzing snowmelt conditions...")

# Identify potential snowmelt conditions:
# - Temperature crosses 0°C from below
# - Snow was present in recent days

# Calculate cumulative snowfall in last 5 days
for days in [1, 2, 3, 4, 5]:
    merged[f'snow_{days}d'] = merged['snowfall'].rolling(window=days*24, min_periods=1).sum()

# Temperature around freezing
merged['temp_near_zero'] = (merged['temperature_2m'].abs() < 2).astype(int)
merged['temp_above_zero'] = (merged['temperature_2m'] > 0).astype(int)
merged['temp_below_zero'] = (merged['temperature_2m'] < 0).astype(int)

# Potential snowmelt: temp above 0 AND snow in last 3 days > 5mm
merged['potential_snowmelt'] = (
    (merged['temperature_2m'] > 0) & 
    (merged['snow_3d'] > 5)
).astype(int)

print(f"Potential snowmelt hours: {merged['potential_snowmelt'].sum()} ({merged['potential_snowmelt'].sum()/len(merged)*100:.2f}%)")

# =============================================================================
# 6. IDENTIFY FLOOD EVENTS
# =============================================================================

print("\nIdentifying flood events...")

# Flood stages for St. Louis
FLOOD_STAGE = 30  # feet
MAJOR_FLOOD = 40  # feet

merged['flood_level'] = pd.cut(
    merged['usgs_level'],
    bins=[-np.inf, FLOOD_STAGE, MAJOR_FLOOD, np.inf],
    labels=['Normal', 'Flood', 'Major Flood']
)

print(f"Normal: {(merged['flood_level'] == 'Normal').sum()} hours ({(merged['flood_level'] == 'Normal').sum()/len(merged)*100:.1f}%)")
print(f"Flood: {(merged['flood_level'] == 'Flood').sum()} hours ({(merged['flood_level'] == 'Flood').sum()/len(merged)*100:.1f}%)")
print(f"Major Flood: {(merged['flood_level'] == 'Major Flood').sum()} hours ({(merged['flood_level'] == 'Major Flood').sum()/len(merged)*100:.1f}%)")

# =============================================================================
# 7. VISUALIZATIONS
# =============================================================================

os.makedirs("Results/weather_features", exist_ok=True)

print("\n=== CREATING VISUALIZATIONS ===")

# 7.1 Correlation analysis (UPDATED)
print("1. Precipitation and soil moisture correlations...")

precip_features = [col for col in merged.columns if col.startswith('precip_lag')]
soil_features = [col for col in merged.columns if 'soil_moisture' in col and 'lag' in col]

all_weather_features = precip_features + soil_features
correlations = merged[all_weather_features + ['usgs_level']].corr()['usgs_level'].drop('usgs_level')

# Separate by type
precip_corr = correlations[correlations.index.str.startswith('precip_lag')]
soil_corr = correlations[correlations.index.str.contains('soil_moisture')]

print("\nTop 10 PRECIPITATION features:")
print(precip_corr.sort_values(ascending=False).head(10))

print("\nTop 10 SOIL MOISTURE features:")
print(soil_corr.sort_values(ascending=False).head(10))

# Create comparison plot
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Precipitation heatmap (same as before)
corr_data = []
for feat in precip_corr.index:
    lag = int(feat.split('lag')[1].split('h_')[0])
    window = int(feat.split('window')[1].split('h')[0])
    corr_data.append({'lag': lag, 'window': window, 'correlation': precip_corr[feat]})

corr_df = pd.DataFrame(corr_data)
corr_pivot = corr_df.pivot(index='window', columns='lag', values='correlation')

sns.heatmap(corr_pivot, annot=True, fmt='.3f', cmap='RdYlGn', center=0, ax=axes[0,0])
axes[0,0].set_title('Precipitation Correlation', fontsize=12, fontweight='bold')

# Precipitation line plot
for lag in corr_pivot.columns:
    axes[0,1].plot(corr_pivot.index, corr_pivot[lag], marker='o', label=f'{lag}h lag')
axes[0,1].set_xlabel('Window (hours)')
axes[0,1].set_ylabel('Correlation')
axes[0,1].set_title('Precipitation vs Window Size', fontsize=12, fontweight='bold')
axes[0,1].legend()
axes[0,1].grid(True, alpha=0.3)

# Soil moisture comparison
if len(soil_corr) > 0:
    # Group by depth and window
    soil_data = []
    for feat in soil_corr.index:
        if '0_to_7cm' in feat:
            depth = 'Surface (0-7cm)'
        elif '7_to_28cm' in feat:
            depth = 'Mid (7-28cm)'
        else:
            depth = 'Deep (28-100cm)'
        
        window = int(feat.split('window')[1].split('h')[0])
        soil_data.append({'depth': depth, 'window': window, 'correlation': soil_corr[feat]})
    
    soil_df = pd.DataFrame(soil_data)
    
    # Plot by depth
    for depth in soil_df['depth'].unique():
        depth_data = soil_df[soil_df['depth'] == depth].groupby('window')['correlation'].max()
        axes[1,0].plot(depth_data.index, depth_data.values, marker='s', label=depth)
    
    axes[1,0].set_xlabel('Window (hours)')
    axes[1,0].set_ylabel('Correlation')
    axes[1,0].set_title('Soil Moisture vs Window Size', fontsize=12, fontweight='bold')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # Top features comparison
    top_precip = precip_corr.max()
    top_soil = soil_corr.max()
    
    axes[1,1].bar(['Precipitation\n(best)', 'Soil Moisture\n(best)'], 
                  [top_precip, top_soil],
                  color=['steelblue', 'brown'])
    axes[1,1].set_ylabel('Max Correlation')
    axes[1,1].set_title('Best Feature Comparison', fontsize=12, fontweight='bold')
    axes[1,1].grid(True, alpha=0.3, axis='y')
    
    for i, v in enumerate([top_precip, top_soil]):
        axes[1,1].text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('Results/weather_features/01_precip_correlations.png', dpi=150)
plt.close()
print("  → Saved: 01_precip_correlations.png")

# 7.2 Heavy rain vs flood events
print("2. Heavy rain indicator vs floods...")

flood_data = merged.groupby(['heavy_rain_48h', 'flood_level']).size().unstack(fill_value=0)
flood_data_pct = flood_data.div(flood_data.sum(axis=1), axis=0) * 100

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

flood_data.plot(kind='bar', ax=axes[0], stacked=False)
axes[0].set_xlabel('Heavy Rain in Last 48h (0=No, 1=Yes)')
axes[0].set_ylabel('Hours')
axes[0].set_title('Flood Events by Heavy Rain Status (Counts)', fontweight='bold')
axes[0].legend(title='Flood Level')
axes[0].set_xticklabels(['No Heavy Rain', 'Heavy Rain'], rotation=0)

flood_data_pct.plot(kind='bar', ax=axes[1], stacked=True)
axes[1].set_xlabel('Heavy Rain in Last 48h (0=No, 1=Yes)')
axes[1].set_ylabel('Percentage')
axes[1].set_title('Flood Events by Heavy Rain Status (%)', fontweight='bold')
axes[1].legend(title='Flood Level')
axes[1].set_xticklabels(['No Heavy Rain', 'Heavy Rain'], rotation=0)

plt.tight_layout()
plt.savefig('Results/weather_features/02_heavy_rain_floods.png', dpi=150)
plt.close()
print("  → Saved: 02_heavy_rain_floods.png")

# 7.3 Snowmelt analysis
print("3. Snowmelt and river level...")

# Filter to winter/spring months where snowmelt is relevant
winter_spring = merged[merged['time'].dt.month.isin([1, 2, 3, 4, 5])]

fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Temperature and snow
ax1 = axes[0]
ax2 = ax1.twinx()

sample = winter_spring[winter_spring['time'].dt.year == 2008]  # Example year
ax1.plot(sample['time'], sample['temperature_2m'], color='red', alpha=0.7, label='Temperature')
ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax2.bar(sample['time'], sample['snowfall'], color='lightblue', alpha=0.5, label='Snowfall', width=0.5)

ax1.set_ylabel('Temperature (°C)', color='red')
ax2.set_ylabel('Snowfall (mm)', color='blue')
ax1.set_title('Temperature and Snowfall (Example: 2008)', fontweight='bold')
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

# Snowmelt vs river level
snowmelt_vs_level = winter_spring.groupby('potential_snowmelt')['usgs_level'].agg(['mean', 'std', 'count'])

axes[1].bar(['No Snowmelt', 'Potential Snowmelt'], 
            snowmelt_vs_level['mean'], 
            yerr=snowmelt_vs_level['std'],
            capsize=5)
axes[1].set_ylabel('Average River Level (ft)')
axes[1].set_title('River Level during Potential Snowmelt Conditions (Winter/Spring)', fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

# Add sample counts
for i, (idx, row) in enumerate(snowmelt_vs_level.iterrows()):
    axes[1].text(i, row['mean'] + row['std'] + 0.5, f"n={row['count']}", 
                ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('Results/weather_features/03_snowmelt_analysis.png', dpi=150)
plt.close()
print("  → Saved: 03_snowmelt_analysis.png")

# 7.4 Best precipitation feature
print("4. Best precipitation feature scatter plot...")

best_feature = correlations.idxmax()
print(f"  Best feature: {best_feature} (correlation: {correlations.max():.3f})")

fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(merged[best_feature], merged['usgs_level'], 
                    c=merged['time'].astype(np.int64), 
                    alpha=0.3, s=1, cmap='viridis')
ax.set_xlabel(f'{best_feature} (mm)', fontsize=11)
ax.set_ylabel('River Level (ft)', fontsize=11)
ax.set_title(f'Best Precipitation Feature vs River Level\n{best_feature}', 
             fontsize=12, fontweight='bold')
ax.axhline(y=FLOOD_STAGE, color='orange', linestyle='--', label='Flood Stage (30 ft)')
ax.axhline(y=MAJOR_FLOOD, color='red', linestyle='--', label='Major Flood (40 ft)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('Results/weather_features/04_best_precip_feature.png', dpi=150)
plt.close()
print("  → Saved: 04_best_precip_feature.png")

# =============================================================================
# 8. SAVE FEATURE SUMMARY
# =============================================================================

print("\n=== FEATURE SUMMARY ===")
print(f"\nBest precipitation feature: {best_feature}")
print(f"Correlation: {correlations.max():.3f}")
print(f"\nTop 5 features:")
print(correlations.sort_values(ascending=False).head())

# Save summary
with open('Results/weather_features/feature_summary.txt', 'w') as f:
    f.write("WEATHER FEATURE ANALYSIS SUMMARY\n")
    f.write("=" * 70 + "\n\n")
    f.write(f"Best precipitation feature: {best_feature}\n")
    f.write(f"Correlation with river level: {correlations.max():.3f}\n\n")
    f.write("Top 5 features:\n")
    f.write(correlations.sort_values(ascending=False).head().to_string())
    f.write("\n\n")
    f.write(f"Heavy rain threshold: {HEAVY_RAIN_THRESHOLD} mm in 48h\n")
    f.write(f"Heavy rain events: {merged['heavy_rain_48h'].sum()} hours\n")
    f.write(f"Potential snowmelt events: {merged['potential_snowmelt'].sum()} hours\n")
    f.write("\n")
    f.write(f"Flood stage: {FLOOD_STAGE} ft\n")
    f.write(f"Major flood: {MAJOR_FLOOD} ft\n")

print("\n✓ Analysis complete! Check Results/weather_features/")
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import numpy as np
import os

# =============================================================================
# 1. DATA LOADING
# =============================================================================

print("Loading data...")
folder = "Data/datasets/"

river_target_st_louis = pd.read_csv(folder + "river_target_st_louis.csv")
river_upstream_grafton = pd.read_csv(folder + "river_upstream_grafton.csv")
river_upstream_hermann = pd.read_csv(folder + "river_upstream_hermann.csv")
weather_history_st_louis = pd.read_csv(folder + "weather_history_st_louis.csv.gz", compression="gzip")

print("Data loaded successfully!\n")

# =============================================================================
# 2. DATE PARSING
# =============================================================================


print("Parsing datetime columns...")
river_target_st_louis['time'] = pd.to_datetime(river_target_st_louis['time']).dt.tz_localize(None)
river_upstream_grafton['time'] = pd.to_datetime(river_upstream_grafton['time']).dt.tz_localize(None)
river_upstream_hermann['time'] = pd.to_datetime(river_upstream_hermann['time']).dt.tz_localize(None)
weather_history_st_louis['datetime'] = pd.to_datetime(weather_history_st_louis['datetime'])

# =============================================================================
# 3. FIND COMMON DATE RANGE AND FILTER
# =============================================================================

print("\n=== ORIGINAL DATE RANGES ===")
print(f"Target St Louis: {river_target_st_louis['time'].min()} to {river_target_st_louis['time'].max()}")
print(f"Grafton: {river_upstream_grafton['time'].min()} to {river_upstream_grafton['time'].max()}")
print(f"Hermann: {river_upstream_hermann['time'].min()} to {river_upstream_hermann['time'].max()}")
print(f"Weather: {weather_history_st_louis['datetime'].min()} to {weather_history_st_louis['datetime'].max()}")

# Find common date range
common_start = max(
    river_target_st_louis['time'].min(),
    river_upstream_grafton['time'].min(),
    river_upstream_hermann['time'].min(),
    weather_history_st_louis['datetime'].min()
)

common_end = min(
    river_target_st_louis['time'].max(),
    river_upstream_grafton['time'].max(),
    river_upstream_hermann['time'].max(),
    weather_history_st_louis['datetime'].max()
)

print(f"\n=== COMMON OVERLAP PERIOD ===")
print(f"From: {common_start}")
print(f"To: {common_end}")

# Filter all datasets to common range
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

print(f"\n=== FILTERED DATA SHAPES ===")
print(f"Target St Louis: {river_target_st_louis.shape}")
print(f"Grafton: {river_upstream_grafton.shape}")
print(f"Hermann: {river_upstream_hermann.shape}")
print(f"Weather: {weather_history_st_louis.shape}")

# =============================================================================
# 4. MISSING VALUES ANALYSIS
# =============================================================================

print("\n=== MISSING VALUES ===")
print(f"Target usgs_level: {river_target_st_louis['usgs_level'].isna().sum()} missing ({river_target_st_louis['usgs_level'].isna().sum()/len(river_target_st_louis)*100:.2f}%)")
print(f"Grafton level: {river_upstream_grafton['grafton_level'].isna().sum()} missing ({river_upstream_grafton['grafton_level'].isna().sum()/len(river_upstream_grafton)*100:.2f}%)")
print(f"Hermann level: {river_upstream_hermann['hermann_level'].isna().sum()} missing ({river_upstream_hermann['hermann_level'].isna().sum()/len(river_upstream_hermann)*100:.2f}%)")

# =============================================================================
# 5. VISUALIZATION
# =============================================================================

os.makedirs("Results/exploration", exist_ok=True)

print("\n=== CREATING VISUALIZATIONS ===")

# 5.1 TIME SERIES PLOT - All river levels
print("Creating time series plot...")
fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)

# Plot each river station
axes[0].plot(river_target_st_louis['time'], river_target_st_louis['usgs_level'], 
             linewidth=0.5, alpha=0.7)
axes[0].set_ylabel('Water Level (ft)', fontsize=10)
axes[0].set_title('Target: St Louis (Hourly)', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3)

axes[1].plot(river_upstream_grafton['time'], river_upstream_grafton['grafton_level'], 
             linewidth=0.8, color='orange')
axes[1].set_ylabel('Water Level (ft)', fontsize=10)
axes[1].set_title('Upstream: Grafton (Daily)', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

axes[2].plot(river_upstream_hermann['time'], river_upstream_hermann['hermann_level'], 
             linewidth=0.8, color='green')
axes[2].set_ylabel('Water Level (ft)', fontsize=10)
axes[2].set_title('Upstream: Hermann (Daily)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Date', fontsize=10)
axes[2].grid(True, alpha=0.3)

# Format x-axis to show years
import matplotlib.dates as mdates
axes[2].xaxis.set_major_locator(mdates.YearLocator())
axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axes[2].xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))  # Jan and Jul
plt.setp(axes[2].xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('Results/exploration/01_timeseries_all_stations.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: 01_timeseries_all_stations.png")

# 5.2 AUTOCORRELATION - Target station
print("Creating autocorrelation plots...")
# Resample target to daily for ACF (too many hourly points)
target_daily = river_target_st_louis.set_index('time')['usgs_level'].resample('D').mean()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

plot_acf(target_daily.dropna(), lags=60, ax=axes[0])
axes[0].set_title('ACF: Target St Louis (Daily Average)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Lag (days)')

plot_pacf(target_daily.dropna(), lags=60, ax=axes[1])
axes[1].set_title('PACF: Target St Louis (Daily Average)', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Lag (days)')

plt.tight_layout()
plt.savefig('Results/exploration/02_autocorrelation_target.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: 02_autocorrelation_target.png")

# 5.3 CROSS-CORRELATION - Upstream vs Target
print("Creating cross-correlation analysis...")
# Merge on date for daily comparison
target_daily_df = target_daily.reset_index()
target_daily_df.columns = ['date', 'target_level']
target_daily_df['date'] = target_daily_df['date'].dt.date

grafton_daily = river_upstream_grafton.copy()
grafton_daily['date'] = grafton_daily['time'].dt.date

hermann_daily = river_upstream_hermann.copy()
hermann_daily['date'] = hermann_daily['time'].dt.date

# Merge all together
merged = target_daily_df.merge(
    grafton_daily[['date', 'grafton_level']], on='date', how='inner'
).merge(
    hermann_daily[['date', 'hermann_level']], on='date', how='inner'
)

# Calculate cross-correlation with different lags
max_lag = 30
lags = range(0, max_lag + 1)
ccf_grafton = []
ccf_hermann = []

for lag in lags:
    if lag == 0:
        ccf_grafton.append(merged[['target_level', 'grafton_level']].corr().iloc[0, 1])
        ccf_hermann.append(merged[['target_level', 'hermann_level']].corr().iloc[0, 1])
    else:
        # Shift upstream data by lag days (upstream leads target)
        lagged_data = merged.copy()
        lagged_data['grafton_lagged'] = lagged_data['grafton_level'].shift(lag)
        lagged_data['hermann_lagged'] = lagged_data['hermann_level'].shift(lag)
        
        ccf_grafton.append(lagged_data[['target_level', 'grafton_lagged']].corr().iloc[0, 1])
        ccf_hermann.append(lagged_data[['target_level', 'hermann_lagged']].corr().iloc[0, 1])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(lags, ccf_grafton, 'o-', label='Grafton → St Louis', linewidth=2, markersize=4)
ax.plot(lags, ccf_hermann, 's-', label='Hermann → St Louis', linewidth=2, markersize=4)
ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
ax.set_xlabel('Lag (days) - Upstream leads Target', fontsize=11)
ax.set_ylabel('Cross-Correlation', fontsize=11)
ax.set_title('Cross-Correlation: Upstream Stations vs Target St Louis', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('Results/exploration/03_cross_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: 03_cross_correlation.png")

# Print correlation summary
print("\n=== CORRELATION SUMMARY ===")
print(f"Grafton → St Louis:")
print(f"  Lag 0: {ccf_grafton[0]:.3f}")
print(f"  Max correlation: {max(ccf_grafton):.3f} at lag {ccf_grafton.index(max(ccf_grafton))} days")
print(f"\nHermann → St Louis:")
print(f"  Lag 0: {ccf_hermann[0]:.3f}")
print(f"  Max correlation: {max(ccf_hermann):.3f} at lag {ccf_hermann.index(max(ccf_hermann))} days")

print("\nExploration complete! Check Results/exploration/ for plots.")

os.makedirs("Results/exploration", exist_ok=True)
print("\nExploration complete!")
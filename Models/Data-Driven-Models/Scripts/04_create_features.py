import pandas as pd
import numpy as np
import argparse
import os

# =============================================================================
# ARGUMENT PARSING
# =============================================================================
parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1, help="Lead time in days (1, 2, 3...)")
args = parser.parse_args()

LEAD_TIME = args.days
print("=" * 70)
print(f"STEP 04: FEATURE ENGINEERING FOR {LEAD_TIME}-DAY LEAD TIME")
print("=" * 70)

# =============================================================================
# 1. LOAD DATA
# =============================================================================
# Load the CLEAN daily dataset (no lags yet)
daily_df = pd.read_csv("Data/processed/daily_flood_dataset.csv")
daily_df['date'] = pd.to_datetime(daily_df['date'])
print(f"  ✓ Loaded: {len(daily_df)} days")

# =============================================================================
# 2. DYNAMIC LAG GENERATION
# =============================================================================
print(f"  Generating features for t+{LEAD_TIME} days...")

# Define history window (relative to the lead time)
# If Lead=2, we use data from t-2, t-3, t-4...
relative_lags = [0, 1, 2, 4, 6]

# 2.1 Upstream & Target Lags
for i in relative_lags:
    actual_lag = LEAD_TIME + i

    # Upstream Stations
    daily_df[f'hermann_lag{actual_lag}d'] = daily_df['hermann_level'].shift(actual_lag)
    daily_df[f'grafton_lag{actual_lag}d'] = daily_df['grafton_level'].shift(actual_lag)

    # Target History (Autoregression)
    if i < 3:  # Keep target history tighter
        daily_df[f'target_lag{actual_lag}d'] = daily_df['target_level_max'].shift(actual_lag)

# 2.2 Weather Lags
# Weather cumulative columns (precip_7d, etc) represent "past 7 days relative to row date".
# We must shift them by LEAD_TIME so we don't peek at tomorrow's rain.
weather_cols = ['precip_7d', 'precip_14d', 'precip_30d', 'soil_deep_30d', 'daily_precip']
for col in weather_cols:
    daily_df[f'{col}_lag{LEAD_TIME}d'] = daily_df[col].shift(LEAD_TIME)

# 2.3 Rolling Stats (Shifted)
# "Average of last 7 days, as known N days ago"
for window in [3, 7, 14]:
    shift_val = LEAD_TIME
    daily_df[f'hermann_ma{window}d'] = daily_df['hermann_level'].shift(shift_val).rolling(window).mean()
    daily_df[f'grafton_ma{window}d'] = daily_df['grafton_level'].shift(shift_val).rolling(window).mean()

# 2.4 Cleanup
# Drop the warm-up period (where lags are NaN)
daily_df = daily_df.dropna().reset_index(drop=True)

# Save to specific file
output_file = f"Data/processed/dataset_L{LEAD_TIME}d.csv"
daily_df.to_csv(output_file, index=False)
print(f"  ✓ Saved: {output_file} ({len(daily_df)} rows)")
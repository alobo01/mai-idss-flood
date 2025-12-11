import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime, timedelta

# --- Configuration ---
TARGET_DATES = [
    "2019-06-08",  # Highest Flood
    "2019-03-31",  # Intermediate (Major)
    "2020-04-11",  # Intermediate (Minor)
    "2023-09-02"  # Lowest Flood
]

STATIONS = {
    'target': '07010000',  # St. Louis
    'hermann': '06934500',
    'grafton': '05587450'
}

PATH = "Programs/use cases/data"


def fetch_and_process_date(target_date_str):
    print(f"\nProcessing target date: {target_date_str}")

    # 1. Define 35-Day Window
    end_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=35)

    str_start = start_date.strftime("%Y-%m-%d")
    str_end = end_date.strftime("%Y-%m-%d")

    # --- 2. Weather (Open-Meteo Archive) ---
    print(f"   ☁️  Fetching Weather ({str_start} to {str_end})...")
    url_w = "https://archive-api.open-meteo.com/v1/archive"
    params_w = {
        "latitude": 38.6270, "longitude": -90.1994,
        "start_date": str_start, "end_date": str_end,
        "daily": ["precipitation_sum"], "timezone": "UTC"
    }

    try:
        r_w = requests.get(url_w, params=params_w).json()
        df_w = pd.DataFrame({
            'date': pd.to_datetime(r_w['daily']['time']),
            'daily_precip': r_w['daily']['precipitation_sum']
        })
    except Exception as e:
        print(f"      ❌ Weather API Error: {e}")
        df_w = pd.DataFrame({'date': pd.date_range(str_start, str_end), 'daily_precip': 0.0})

    # --- 3. Rivers (USGS Historical) ---
    dfs_river = {}

    for name, site in STATIONS.items():
        print(f"   🌊 Fetching {name.capitalize()} ({site})...")

        # Prepare fallback
        dfs_river[name] = pd.DataFrame({'date': pd.date_range(str_start, str_end), f'{name}_level': np.nan})

        url_r = "https://waterservices.usgs.gov/nwis/iv/"
        params_r = {
            'format': 'json',
            'sites': site,
            'startDT': str_start,
            'endDT': str_end,
            'parameterCd': '00065'  # Gauge Height
        }

        try:
            r_r = requests.get(url_r, params=params_r).json()

            if 'value' in r_r and 'timeSeries' in r_r['value'] and r_r['value']['timeSeries']:
                vals_list = r_r['value']['timeSeries'][0]['values'][0]['value']
                if vals_list:
                    # Parse 15-min data
                    temp_df = pd.DataFrame(vals_list)
                    temp_df['value'] = pd.to_numeric(temp_df['value'])

                    # FIX: Handle mixed timezones (DST) by enforcing UTC
                    temp_df['dateTime'] = pd.to_datetime(temp_df['dateTime'], utc=True).dt.tz_convert(None)

                    # Resample to Daily Mean
                    temp_df['date'] = temp_df['dateTime'].dt.floor('D')
                    daily_mean = temp_df.groupby('date')['value'].mean().reset_index()

                    dfs_river[name] = pd.DataFrame({
                        'date': daily_mean['date'],
                        f'{name}_level': daily_mean['value']
                    })
        except Exception as e:
            print(f"      ⚠️ API Error for {name}: {e}")

    # --- 4. Merge Data ---
    df_merged = df_w.copy()
    for name in STATIONS:
        df_merged = df_merged.merge(dfs_river[name], on='date', how='left')

    # --- 5. Clean & Interpolate ---
    df_merged['daily_precip'] = df_merged['daily_precip'].fillna(0.0)

    for name in STATIONS:
        col = f"{name}_level"
        # Interpolate small gaps
        df_merged[col] = df_merged[col].interpolate(method='linear', limit_direction='both')
        # FIX: Use new ffill/bfill syntax
        df_merged[col] = df_merged[col].ffill().bfill()

    # Rename target for compatibility with model
    df_merged = df_merged.rename(columns={'target_level': 'target_level_max'})

    # --- 6. Save to Script's Directory ---
    filename = f"prediction_data_{target_date_str}.csv"

    # Get the folder where THIS script is running
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filename)

    try:
        df_merged.to_csv(full_path, index=False)
        print(f"   ✅ Saved: {full_path}")
    except PermissionError:
        print(f"   ❌ ERROR: Could not save {filename}. It might be open in Excel.")


# --- Execution ---
if __name__ == "__main__":
    for date_str in TARGET_DATES:
        fetch_and_process_date(date_str)